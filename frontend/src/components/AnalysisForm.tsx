import { Sparkles, Image, Upload, Edit3, Loader2, AlertTriangle, FileText } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { ScrollInput } from "./ScrollInput";
import { ResultsDisplay } from "./ResultsDisplay";
import { useAPIInfo, useIdentifyText, useIdentifyFile, useExtractText } from "../hooks/useApi";
import type { AnalysisMode, IdentifyResponse } from "../types/api";

// Fixed analysis settings
const ANALYSIS_MODE: AnalysisMode = "line";
const OUTPUT_SCRIPT = "";

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
  
  // Image/File state
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // OCR extracted text state
  const [extractedText, setExtractedText] = useState<string | null>(null);
  
  // Refs for file inputs
  const imageInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  
  // Results state
  const [result, setResult] = useState<IdentifyResponse | null>(null);
  const [resultType, setResultType] = useState<"text" | "image" | "file">("text");
  
  // API hooks
  const { connected } = useAPIInfo();
  const { loading: textLoading, error: textError, identify: identifyText } = useIdentifyText();
  const { loading: fileLoading, error: fileError, identify: identifyFile } = useIdentifyFile();
  const { loading: extractLoading, error: extractError, extract: extractTextFromImage } = useExtractText();
  
  const isLoading = textLoading || fileLoading;
  const error = textError || fileError || extractError;

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
      setSelectedImage(file);
      setExtractedText(null); // Reset extracted text when new image selected
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
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
      const response = await identifyText(extractedText, ANALYSIS_MODE, OUTPUT_SCRIPT);
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
        response = await identifyText(text, ANALYSIS_MODE, OUTPUT_SCRIPT);
        setResultType("text");
      } else if (activeTab === "file") {
        if (!selectedFile) {
          alert("Please select a file");
          return;
        }
        response = await identifyFile(selectedFile, ANALYSIS_MODE, OUTPUT_SCRIPT);
        setResultType("file");
      } else {
        return; // Image tab has its own flow
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
            className={`tab-button flex-1 border transition-all duration-300 ${
              activeTab === "text"
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
            className={`tab-button flex-1 border transition-all duration-300 ${
              activeTab === "image"
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
            className={`tab-button flex-1 border transition-all duration-300 ${
              activeTab === "file"
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
                  className={`group border-2 border-dashed border-[var(--color-border-subtle)] rounded-[20px] p-8 bg-gradient-to-b from-white to-[#fdf8f3] transition-all duration-300 ${
                    !selectedImage ? 'cursor-pointer hover:from-white hover:to-[var(--color-primary-soft)] hover:border-[var(--color-primary)] hover:shadow-xl' : ''
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
                          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] transition-all duration-300 shadow-lg hover:shadow-xl font-semibold text-base disabled:opacity-50"
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
                          className="flex items-center gap-2 px-6 py-3 bg-white border-2 border-red-400 text-red-500 rounded-full hover:bg-red-50 hover:border-red-500 transition-all duration-300 font-semibold text-base"
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
                      <div className="p-6 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] rounded-2xl shadow-lg group-hover:shadow-xl group-hover:scale-110 transition-all duration-300">
                        <Image className="w-10 h-10 text-white" />
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-semibold text-[var(--color-text-main)] mb-2">
                          Drop your image here
                        </p>
                        <p className="text-[var(--color-text-muted)] text-base mb-1">
                          or click to browse
                        </p>
                        <p className="text-[var(--color-text-muted)] text-sm">
                          Supports PNG, JPG, JPEG (max 10MB)
                        </p>
                      </div>
                      <button className="px-8 py-3 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] transition-all duration-300 shadow-lg hover:shadow-xl font-semibold text-base group-hover:scale-105">
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
                  <div className="text-xl font-semibold text-[var(--color-text-main)] leading-loose mb-8 whitespace-pre-wrap p-8 bg-white rounded-[16px] border border-[var(--color-border-subtle)]">
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
            <div>
              <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base">
                Upload Document File
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.text"
                onChange={handleFileSelect}
                className="hidden"
              />
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="group border-2 border-dashed border-[var(--color-border-subtle)] rounded-[20px] p-12 bg-gradient-to-b from-white to-[#fdf8f3] hover:from-white hover:to-[var(--color-primary-soft)] transition-all duration-300 cursor-pointer hover:border-[var(--color-primary)] hover:shadow-xl"
              >
                {selectedFile ? (
                  <div className="flex flex-col items-center gap-6">
                    <div className="relative">
                      <div className="p-6 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] rounded-2xl shadow-lg">
                        <Upload className="w-10 h-10 text-white" />
                      </div>
                      <div className="absolute -top-2 -right-2 p-2 bg-green-500 rounded-full shadow-md">
                        <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold text-[var(--color-text-main)] mb-1">
                        {selectedFile.name}
                      </p>
                      <p className="text-sm text-[var(--color-text-muted)]">
                        Click to change file
                      </p>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                      }}
                      className="flex items-center gap-2 text-sm text-red-500 hover:text-red-600 font-medium hover:underline px-4 py-2 rounded-full hover:bg-red-50 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Remove File
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-6">
                    <div className="p-6 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] rounded-2xl shadow-lg group-hover:shadow-xl group-hover:scale-110 transition-all duration-300">
                      <Upload className="w-10 h-10 text-white" />
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold text-[var(--color-text-main)] mb-2">
                        Drop your file here
                      </p>
                      <p className="text-[var(--color-text-muted)] text-base mb-1">
                        or click to browse
                      </p>
                      <p className="text-[var(--color-text-muted)] text-sm">
                        Supports TXT files only
                      </p>
                    </div>
                    <button className="px-8 py-3 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white rounded-full hover:from-[var(--color-primary-dark)] hover:to-[#D96E12] transition-all duration-300 shadow-lg hover:shadow-xl font-semibold text-base group-hover:scale-105">
                      Choose File
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Bottom Action Row - Only show for text and file tabs */}
        {activeTab !== "image" && (
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
