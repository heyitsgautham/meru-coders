import { Sparkles, Image, Upload, Edit3, Loader2, AlertTriangle, FileText, BookOpen } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { ScrollInput } from "./ScrollInput";
import { ResultsDisplay } from "./ResultsDisplay";
import { useAPIInfo, useIdentifyText, useIdentifyFile, useExtractText, useExtractFile } from "../hooks/useApi";
import type { AnalysisMode, IdentifyResponse, FileInfo, IdentificationMode } from "../types/api";

// Fixed analysis settings
const ANALYSIS_MODE: AnalysisMode = "verse";
const OUTPUT_SCRIPT = "";

// Mode descriptions for UI
const MODE_INFO: Record<IdentificationMode, { label: string; description: string }> = {
  auto: {
    label: "Auto Detect",
    description: "Automatically chooses the best identification method based on text characteristics"
  },
  vedic: {
    label: "Vedic Mode",
    description: "Optimized for Vedic meters (Gayatri, Trishtubh, Jagati) using syllable-count detection"
  },
  classical: {
    label: "Classical Mode",
    description: "For classical Sanskrit meters using L-G pattern matching (Anushtubh, Vasantatilaka)"
  }
};

// LocalStorage keys
const STORAGE_KEYS = {
  activeTab: 'chanda_activeTab',
};

interface AnalysisFormProps {
  initialText?: string;
  onTextChange?: (text: string) => void;
}

export function AnalysisForm({ initialText = "", onTextChange }: AnalysisFormProps) {
  const [text, setText] = useState(initialText);
  const [activeTab, setActiveTab] = useState<"text" | "image" | "file">(() => {
    const saved = localStorage.getItem(STORAGE_KEYS.activeTab);
    return (saved as "text" | "image" | "file") || "text";
  });

  // Identification mode state
  const [identificationMode, setIdentificationMode] = useState<IdentificationMode>("auto");

  // Image/File state
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // OCR extracted text state
  const [extractedText, setExtractedText] = useState<string | null>(null);

  // File extracted text state (for DOCX/TXT)
  const [fileExtractedText, setFileExtractedText] = useState<string | null>(null);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [fileWarnings, setFileWarnings] = useState<string[]>([]);

  // Refs for file inputs
  const imageInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Drag and drop state
  const [isDraggingImage, setIsDraggingImage] = useState(false);
  const [isDraggingFile, setIsDraggingFile] = useState(false);

  // Results state
  const [result, setResult] = useState<IdentifyResponse | null>(null);
  const [resultType, setResultType] = useState<"text" | "image" | "file">("text");

  // API hooks
  const { connected } = useAPIInfo();
  const { loading: textLoading, error: textError, identify: identifyText } = useIdentifyText();
  const { loading: fileLoading, error: fileError, identify: identifyFile } = useIdentifyFile();
  const { loading: extractLoading, error: extractError, extract: extractTextFromImage } = useExtractText();
  const {
    loading: fileExtractLoading,
    error: fileExtractError,
    errorDetails: fileExtractErrorDetails,
    extract: extractTextFromFile,
    reset: resetFileExtract
  } = useExtractFile();

  const isLoading = textLoading || fileLoading;
  const error = textError || fileError || extractError || fileExtractError;

  // Save activeTab to localStorage when it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.activeTab, activeTab);
  }, [activeTab]);

  // Scroll to results when they appear
  useEffect(() => {
    if (result && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [result]);

  // Sync text with parent when initialText changes
  useEffect(() => {
    if (initialText) {
      setText(initialText);
      setActiveTab("text");
    }
  }, [initialText]);

  // Notify parent of text changes
  const handleTextChange = (newText: string) => {
    setText(newText);
    onTextChange?.(newText);
  };

  // Handle image selection
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processImageFile(file);
    }
  };

  // Process image file (shared between select and drag-drop)
  const processImageFile = (file: File) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }
    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      alert('Image size must be less than 10MB');
      return;
    }
    setSelectedImage(file);
    setExtractedText(null); // Reset extracted text when new image selected
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  // Handle drag events for image upload
  const handleImageDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleImageDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingImage(true);
  };

  const handleImageDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set to false if we're leaving the drop zone entirely
    if (e.currentTarget.contains(e.relatedTarget as Node)) {
      return;
    }
    setIsDraggingImage(false);
  };

  const handleImageDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingImage(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      processImageFile(file);
    }
  };

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processDocumentFile(file);
    }
  };

  // Process document file (DOCX, TXT)
  const processDocumentFile = (file: File) => {
    // Validate file extension
    const ext = file.name.split('.').pop()?.toLowerCase();
    const allowedExtensions = ['docx', 'txt', 'text'];

    if (!ext || !allowedExtensions.includes(ext)) {
      alert('Please select a DOCX or TXT file');
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    setFileExtractedText(null);
    setFileInfo(null);
    resetFileExtract();
  };

  // Handle drag events for file upload
  const handleFileDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleFileDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingFile(true);
  };

  const handleFileDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget as Node)) {
      return;
    }
    setIsDraggingFile(false);
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingFile(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      processDocumentFile(file);
    }
  };

  // Handle file text extraction
  const handleExtractFileText = async () => {
    if (!selectedFile) return;

    try {
      const response = await extractTextFromFile(selectedFile);
      if (response.success && response.text) {
        setFileExtractedText(response.text);
        setFileInfo(response.file_info || null);
        setFileWarnings(response.warnings || []);
      }
    } catch (err) {
      console.error("File extraction failed:", err);
    }
  };

  // Handle "Identify Chandas" from extracted file text
  const handleIdentifyFromFile = async () => {
    if (!fileExtractedText) return;

    // Set the text and switch to text tab
    setText(fileExtractedText);
    setActiveTab("text");
    setResult(null);

    try {
      const response = await identifyText(fileExtractedText, ANALYSIS_MODE, OUTPUT_SCRIPT);
      setResultType("text");
      setResult(response);
    } catch (err) {
      console.error("Analysis failed:", err);
    }
  };

  // Clear file and reset state
  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFileExtractedText(null);
    setFileInfo(null);
    setFileWarnings([]);
    resetFileExtract();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Get file type icon based on extension
  const getFileTypeIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'docx':
        return '📝';
      default:
        return '📃';
    }
  };

  // Get file type label
  const getFileTypeLabel = (fileType: string) => {
    switch (fileType) {
      case 'docx':
        return 'Word Document';
      case 'txt':
        return 'Text File';
      default:
        return 'Document';
    }
  };

  // Handle OCR text extraction
  const handleExtractText = async () => {
    if (!selectedImage) {
      return;
    }

    try {
      const text = await extractTextFromImage(selectedImage);
      setExtractedText(text);
    } catch (err) {
      console.error("OCR extraction failed:", err);
    }
  };

  // Handle "Identify Chandas" from OCR - auto-insert text and analyze
  const handleIdentifyFromOCR = async () => {
    if (!extractedText) return;

    // Set the text and switch to text tab
    setText(extractedText);
    setActiveTab("text");
    setResult(null);

    try {
      const response = await identifyText(extractedText, ANALYSIS_MODE, OUTPUT_SCRIPT, identificationMode);
      setResultType("text");
      setResult(response);
    } catch (err) {
      console.error("Analysis failed:", err);
    }
  };

  // Handle form submission
  const handleSubmit = async () => {
    setResult(null);

    try {
      let response: IdentifyResponse;

      if (activeTab === "text") {
        if (!text.trim()) {
          alert("Please enter some Sanskrit text");
          return;
        }
        response = await identifyText(text, ANALYSIS_MODE, OUTPUT_SCRIPT, identificationMode);
        setResultType("text");
      } else if (activeTab === "file") {
        if (!selectedFile) {
          alert("Please select a file");
          return;
        }
        response = await identifyFile(selectedFile, ANALYSIS_MODE, OUTPUT_SCRIPT, identificationMode);
        setResultType("file");
      } else {
        return; // Image and File tabs have their own flows
      }

      setResult(response);
    } catch (err) {
      console.error("Analysis failed:", err);
    }
  };

  const handleCloseResults = () => {
    setResult(null);
  };

  // Clear image and reset state
  const handleRemoveImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setExtractedText(null);
    // Reset the file input so the same file can be selected again
    if (imageInputRef.current) {
      imageInputRef.current.value = '';
    }
  };

  return (
    <>
      {/* Main Form Container - constrained to 900px and centered */}
      <div style={{ width: '900px', maxWidth: '100%', margin: '0 auto' }} className="animate-fadeIn">
        {/* API Connection Warning */}
        {!connected && (
          <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-[12px] flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-700">Backend API not connected</p>
              <p className="text-sm text-amber-600">Make sure the backend is running at <code className="bg-amber-100 px-1 rounded">http://localhost:5000</code></p>
            </div>
          </div>
        )}

        {/* Main card */}
        <div className="main-card">
          {/* Title Block */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-3 mb-4">
              <div className="h-px w-12 bg-gradient-to-r from-transparent via-[var(--color-accent-gold)] to-[var(--color-primary)]" />
              <Sparkles className="w-4 h-4 text-[var(--color-accent-amber)]" />
              <div className="h-px w-12 bg-gradient-to-l from-transparent via-[var(--color-accent-gold)] to-[var(--color-primary)]" />
            </div>
            <h1 className="text-center mb-2">
              Analyze Sanskrit Text
            </h1>
            <p className="subtitle-text">
              Choose your input method and identify the meter
            </p>
          </div>

          {/* Tabs */}
          <div className="flex items-stretch gap-2.5" style={{ marginBottom: '40px' }}>
            {/* Text Input Tab */}
            <button
              onClick={() => {
                setActiveTab("text");
                setResult(null); // Clear results when switching tabs
              }}
              className={`tab-button flex-1 border transition-all duration-300 ${activeTab === "text"
                ? "border-[var(--color-primary)] bg-[var(--color-primary-soft)] text-[var(--color-primary-dark)] shadow-[0_0_0_1px_rgba(255,153,51,0.35)]"
                : "border-[var(--color-border-subtle)] bg-white text-[var(--color-text-main)] hover:border-[var(--color-accent-gold)] hover:bg-[var(--color-primary-soft)]"
                }`}
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span className="text-sm font-medium">Text Input</span>
            </button>

            {/* Image OCR Tab */}
            <button
              onClick={() => {
                setActiveTab("image");
                setResult(null); // Clear results when switching tabs
              }}
              className={`tab-button flex-1 border transition-all duration-300 ${activeTab === "image"
                ? "border-[var(--color-primary)] bg-[var(--color-primary-soft)] text-[var(--color-primary-dark)] shadow-[0_0_0_1px_rgba(255,153,51,0.35)]"
                : "border-[var(--color-border-subtle)] bg-white text-[var(--color-text-main)] hover:border-[var(--color-accent-gold)] hover:bg-[var(--color-primary-soft)]"
                }`}
            >
              <Image className="w-3.5 h-3.5" />
              <span className="text-sm font-medium">Image OCR</span>
            </button>

            {/* File Upload Tab */}
            <button
              onClick={() => {
                setActiveTab("file");
                setResult(null); // Clear results when switching tabs
              }}
              className={`tab-button flex-1 border transition-all duration-300 ${activeTab === "file"
                ? "border-[var(--color-primary)] bg-[var(--color-primary-soft)] text-[var(--color-primary-dark)] shadow-[0_0_0_1px_rgba(255,153,51,0.35)]"
                : "border-[var(--color-border-subtle)] bg-white text-[var(--color-text-main)] hover:border-[var(--color-accent-gold)] hover:bg-[var(--color-primary-soft)]"
                }`}
            >
              <Upload className="w-3.5 h-3.5" />
              <span className="text-sm font-medium">File Upload</span>
            </button>
          </div>

          {/* Tab Content */}
          <div className="field-group--textarea">
            {activeTab === "text" && (
              <div>
                <ScrollInput
                  value={text}
                  onChange={handleTextChange}
                  placeholder="Type or paste your Sanskrit shloka here…"
                />
              </div>
            )}

            {activeTab === "image" && (
              <div className="space-y-6">
                {/* Image Upload Area */}
                <div>
                  <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base">
                    Upload Image for OCR
                  </label>
                  <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    className="hidden"
                  />
                  <div
                    onClick={() => !selectedImage && imageInputRef.current?.click()}
                    onDragOver={handleImageDragOver}
                    onDragEnter={handleImageDragEnter}
                    onDragLeave={handleImageDragLeave}
                    onDrop={handleImageDrop}
                    className={`group border-2 border-dashed rounded-[20px] p-8 bg-gradient-to-b transition-all duration-300 ${isDraggingImage
                      ? 'border-[var(--color-primary)] bg-[var(--color-primary-soft)] shadow-xl scale-[1.02]'
                      : selectedImage
                        ? 'border-[var(--color-border-subtle)] from-white to-[#fdf8f3]'
                        : 'border-[var(--color-border-subtle)] from-white to-[#fdf8f3] cursor-pointer hover:from-white hover:to-[var(--color-primary-soft)] hover:border-[var(--color-primary)] hover:shadow-xl'
                      }`}
                  >
                    {imagePreview ? (
                      <div className="flex flex-col items-center gap-6">
                        <div className="relative">
                          <img
                            src={imagePreview}
                            alt="Preview"
                            className="max-h-56 rounded-xl shadow-lg border-4 border-white"
                          />
                          {/* Remove button on image */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRemoveImage();
                            }}
                            className="absolute -top-3 -right-3 p-2 bg-red-500 hover:bg-red-600 rounded-full shadow-lg transition-all duration-200 hover:scale-110"
                            title="Remove image"
                          >
                            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                        <div className="text-center">
                          <p className="text-base font-medium text-[var(--color-text-main)] mb-1">
                            {selectedImage?.name}
                          </p>
                        </div>

                        {/* Extract Text Button - only show when no extracted text */}
                        {!extractedText && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleExtractText();
                            }}
                            disabled={extractLoading}
                            className="px-8 py-3 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] transition-all duration-300 shadow-lg hover:shadow-xl font-semibold text-base disabled:opacity-50 flex items-center gap-2"
                          >
                            {extractLoading ? (
                              <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>Extracting...</span>
                              </>
                            ) : (
                              <>
                                <FileText className="w-5 h-5" />
                                <span>Extract Text</span>
                              </>
                            )}
                          </button>
                        )}

                        {/* Clear Image Button - only show after text extraction */}
                        {extractedText && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRemoveImage();
                            }}
                            className="px-8 py-3 bg-[var(--color-primary-soft)] text-[var(--color-primary-dark)] border border-[var(--color-primary)] rounded-full hover:bg-[var(--color-primary)] hover:text-white transition-all duration-300 shadow-md hover:shadow-lg font-semibold text-base flex items-center gap-2"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            <span>Clear Image</span>
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-6">
                        <div className={`p-6 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] rounded-2xl shadow-lg transition-all duration-300 ${isDraggingImage ? 'scale-110 shadow-xl' : 'group-hover:shadow-xl group-hover:scale-110'
                          }`}>
                          <Image className="w-10 h-10 text-white" />
                        </div>
                        <div className="text-center">
                          <p className="text-lg font-semibold text-[var(--color-text-main)] mb-2">
                            {isDraggingImage ? 'Drop your image here!' : 'Drop your image here'}
                          </p>
                          <p className="text-[var(--color-text-muted)] text-base mb-1">
                            or click to browse
                          </p>
                          <p className="text-[var(--color-text-muted)] text-sm">
                            Supports PNG, JPG, JPEG (max 10MB)
                          </p>
                        </div>
                        <button className={`px-8 py-3 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] transition-all duration-300 shadow-lg hover:shadow-xl font-semibold text-base ${isDraggingImage ? 'scale-105' : 'group-hover:scale-105'
                          }`}>
                          Choose File
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Extracted Text Display - Styled with theme border */}
                {extractedText && (
                  <div className="mt-8 p-8 bg-[#fdf8f3] border-2 border-[var(--color-primary)] rounded-[20px] shadow-md">
                    {/* Extracted Text Heading */}
                    <h3 className="text-2xl font-bold text-[var(--color-text-main)] mb-6">
                      Extracted Text
                    </h3>

                    {/* Text Content */}
                    <div
                      className="text-center mb-8 whitespace-pre-wrap p-8 bg-white rounded-[16px] border border-[var(--color-border-subtle)]"
                      style={{
                        fontFamily: "'Crimson Text', 'Merriweather', Georgia, 'Times New Roman', serif",
                        fontSize: '25px',
                        fontWeight: 400,
                        color: '#4a2c10',
                        lineHeight: 1.75,
                        letterSpacing: '0.02em'
                      }}
                    >
                      {extractedText}
                    </div>

                    {/* Button Row */}
                    <div className="flex items-center gap-4">
                      {/* Identify Chandas Button */}
                      <button
                        onClick={handleIdentifyFromOCR}
                        disabled={textLoading}
                        className="identify-btn h-[52px] px-8 text-base"
                      >
                        {textLoading ? (
                          <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>Analyzing...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-5 h-5" />
                            <span>Identify Chandas</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "file" && (
              <div className="space-y-6">
                {/* File Upload Area */}
                <div>
                  <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base">
                    Upload Document File
                  </label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".docx,.txt,.text"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <div
                    onClick={() => !selectedFile && fileInputRef.current?.click()}
                    onDragOver={handleFileDragOver}
                    onDragEnter={handleFileDragEnter}
                    onDragLeave={handleFileDragLeave}
                    onDrop={handleFileDrop}
                    className={`group border-2 border-dashed rounded-[20px] p-8 bg-gradient-to-b transition-all duration-300 ${isDraggingFile
                      ? 'border-[var(--color-primary)] bg-[var(--color-primary-soft)] shadow-xl scale-[1.02]'
                      : selectedFile
                        ? 'border-[var(--color-border-subtle)] from-white to-[#fdf8f3]'
                        : 'border-[var(--color-border-subtle)] from-white to-[#fdf8f3] cursor-pointer hover:from-white hover:to-[var(--color-primary-soft)] hover:border-[var(--color-primary)] hover:shadow-xl'
                      }`}
                  >
                    {selectedFile ? (
                      <div className="flex flex-col items-center gap-6">
                        <div className="relative">
                          <div className="p-6 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] rounded-2xl shadow-lg">
                            <span className="text-4xl">{getFileTypeIcon(selectedFile.name)}</span>
                          </div>
                          {/* Remove button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRemoveFile();
                            }}
                            className="absolute -top-3 -right-3 p-2 bg-red-500 hover:bg-red-600 rounded-full shadow-lg transition-all duration-200 hover:scale-110"
                            title="Remove file"
                          >
                            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                        <div className="text-center">
                          <p className="text-lg font-semibold text-[var(--color-text-main)] mb-1">
                            {selectedFile.name}
                          </p>
                          <p className="text-sm text-[var(--color-text-muted)]">
                            {(selectedFile.size / 1024).toFixed(1)} KB
                          </p>
                        </div>

                        {/* Extract Text Button - only show when no extracted text */}
                        {!fileExtractedText && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleExtractFileText();
                            }}
                            disabled={fileExtractLoading}
                            className="px-8 py-3 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] transition-all duration-300 shadow-lg hover:shadow-xl font-semibold text-base disabled:opacity-50 flex items-center gap-2"
                          >
                            {fileExtractLoading ? (
                              <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>Extracting...</span>
                              </>
                            ) : (
                              <>
                                <FileText className="w-5 h-5" />
                                <span>Extract Text</span>
                              </>
                            )}
                          </button>
                        )}

                        {/* Clear File Button - only show after text extraction */}
                        {fileExtractedText && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRemoveFile();
                            }}
                            className="px-8 py-3 bg-[var(--color-primary-soft)] text-[var(--color-primary-dark)] border border-[var(--color-primary)] rounded-full hover:bg-[var(--color-primary)] hover:text-white transition-all duration-300 shadow-md hover:shadow-lg font-semibold text-base flex items-center gap-2"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            <span>Clear File</span>
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-6">
                        <div className={`p-6 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] rounded-2xl shadow-lg transition-all duration-300 ${isDraggingFile ? 'scale-110 shadow-xl' : 'group-hover:shadow-xl group-hover:scale-110'
                          }`}>
                          <Upload className="w-10 h-10 text-white" />
                        </div>
                        <div className="text-center">
                          <p className="text-lg font-semibold text-[var(--color-text-main)] mb-2">
                            {isDraggingFile ? 'Drop your file here!' : 'Drop your file here'}
                          </p>
                          <p className="text-[var(--color-text-muted)] text-base mb-1">
                            or click to browse
                          </p>
                          <p className="text-[var(--color-text-muted)] text-sm">
                            Supports DOCX, TXT (max 10MB)
                          </p>
                        </div>
                        <button className={`px-8 py-3 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] transition-all duration-300 shadow-lg hover:shadow-xl font-semibold text-base ${isDraggingFile ? 'scale-105' : 'group-hover:scale-105'
                          }`}>
                          Choose File
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* File Extraction Error Display */}
                {fileExtractError && (
                  <div className="mt-4 p-5 bg-red-50 border-2 border-red-200 rounded-[16px] flex items-start gap-4">
                    <div className="p-2 bg-red-100 rounded-full">
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-red-700 mb-1">Extraction Failed</p>
                      <p className="text-red-600">{fileExtractError}</p>
                      {fileExtractErrorDetails && (
                        <p className="text-sm text-red-500 mt-2">{fileExtractErrorDetails}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Extracted Text Display - Styled with theme border */}
                {fileExtractedText && (
                  <div className="mt-8 p-8 bg-[#fdf8f3] border-2 border-[var(--color-primary)] rounded-[20px] shadow-md">
                    {/* Extracted Text Heading with File Info */}
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-2xl font-bold text-[var(--color-text-main)]">
                        Extracted Text
                      </h3>
                      {fileInfo && (
                        <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
                          <span className="px-3 py-1 bg-white rounded-full border border-[var(--color-border-subtle)]">
                            {getFileTypeLabel(fileInfo.file_type)}
                          </span>
                          {fileInfo.page_count > 1 && (
                            <span className="px-3 py-1 bg-white rounded-full border border-[var(--color-border-subtle)]">
                              {fileInfo.page_count} pages
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Warning Banner for CID encoding issues */}
                    {fileWarnings.length > 0 && (
                      <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-[12px] flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-medium text-amber-700">Extraction Warning</p>
                          {fileWarnings.map((warning, idx) => (
                            <p key={idx} className="text-sm text-amber-600 mt-1">{warning}</p>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Text Content */}
                    <div
                      className="text-center mb-8 whitespace-pre-wrap p-8 bg-white rounded-[16px] border border-[var(--color-border-subtle)] max-h-[400px] overflow-y-auto"
                      style={{
                        fontFamily: "'Crimson Text', 'Merriweather', Georgia, 'Times New Roman', serif",
                        fontSize: '25px',
                        fontWeight: 400,
                        color: '#4a2c10',
                        lineHeight: 1.75,
                        letterSpacing: '0.02em'
                      }}
                    >
                      {fileExtractedText}
                    </div>

                    {/* Button Row */}
                    <div className="flex items-center gap-4">
                      {/* Identify Chandas Button */}
                      <button
                        onClick={handleIdentifyFromFile}
                        disabled={textLoading}
                        className="identify-btn h-[52px] px-8 text-base"
                      >
                        {textLoading ? (
                          <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>Analyzing...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-5 h-5" />
                            <span>Identify Chandas</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Identification Mode Selector - Only show for text tab */}
          {activeTab === "text" && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-[var(--color-primary)]" />
                  <span className="text-sm font-semibold text-[var(--color-text-main)]">Detection Mode</span>
                </div>
                <span className="text-xs text-[var(--color-text-muted)]">
                  {MODE_INFO[identificationMode].description}
                </span>
              </div>
              <div className="inline-flex rounded-lg border border-[var(--color-border-subtle)] p-1 bg-[#faf7f4]">
                {(Object.keys(MODE_INFO) as IdentificationMode[]).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setIdentificationMode(mode)}
                    className={`px-5 py-2 rounded-md text-sm font-medium transition-all duration-200 ${identificationMode === mode
                        ? "bg-white text-[var(--color-primary-dark)] shadow-sm border border-[var(--color-primary-light)]"
                        : "text-[var(--color-text-muted)] hover:text-[var(--color-text-main)]"
                      }`}
                  >
                    {MODE_INFO[mode].label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Bottom Action Row - Only show for text tab */}
          {activeTab === "text" && (
            <div className="mt-8 pt-6 border-t border-[var(--color-border-subtle)] bg-[#fdf8f3] -mx-8 px-8 py-6 -mb-8 rounded-b-[20px] flex justify-center">
              {/* Identify Button */}
              <button
                className="identify-btn h-[52px] px-8 text-base"
                onClick={handleSubmit}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    <span>Identify Chanda</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-6 p-5 bg-red-50 border-2 border-red-200 rounded-[16px] flex items-start gap-4">
              <div className="p-2 bg-red-100 rounded-full">
                <AlertTriangle className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <p className="font-semibold text-red-700 mb-1">Error</p>
                <p className="text-red-600">{error}</p>
              </div>
            </div>
          )}
        </div>
      </div>{/* End of 900px constrained container */}

      {/* Results Display - SEPARATE container, wider width - Only show for text input tab */}
      {result && activeTab === "text" && (
        <div ref={resultsRef} style={{ width: '1400px', maxWidth: '100%', margin: '40px auto 0 auto' }}>
          <ResultsDisplay
            result={result}
            type={resultType}
            onClose={handleCloseResults}
          />
        </div>
      )}
    </>
  );
}
