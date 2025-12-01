import { Sparkles, Image, Upload, Edit3, Loader2, AlertTriangle } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { ScrollInput } from "./ScrollInput";
import { ResultsDisplay } from "./ResultsDisplay";
import { useSchemes, useAPIInfo, useIdentifyText, useIdentifyImage, useIdentifyFile } from "../hooks/useApi";
import type { AnalysisMode, OCREngine, IdentifyResponse } from "../types/api";

interface AnalysisFormProps {
  initialText?: string;
  onTextChange?: (text: string) => void;
}

export function AnalysisForm({ initialText = "", onTextChange }: AnalysisFormProps) {
  const [text, setText] = useState(initialText);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("line");
  const [outputScript, setOutputScript] = useState("");
  const [activeTab, setActiveTab] = useState<"text" | "image" | "file">("text");
  
  // Image/File state
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ocrEngine, setOcrEngine] = useState<OCREngine>("tesseract");
  
  // Refs for file inputs
  const imageInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Results state
  const [result, setResult] = useState<IdentifyResponse | null>(null);
  const [resultType, setResultType] = useState<"text" | "image" | "file">("text");
  
  // API hooks
  const { schemes } = useSchemes();
  const { ocrAvailable, connected } = useAPIInfo();
  const { loading: textLoading, error: textError, identify: identifyText } = useIdentifyText();
  const { loading: imageLoading, error: imageError, identify: identifyImage } = useIdentifyImage();
  const { loading: fileLoading, error: fileError, identify: identifyFile } = useIdentifyFile();
  
  const isLoading = textLoading || imageLoading || fileLoading;
  const error = textError || imageError || fileError;

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
        response = await identifyText(text, analysisMode, outputScript);
        setResultType("text");
      } else if (activeTab === "image") {
        if (!selectedImage) {
          alert("Please select an image");
          return;
        }
        response = await identifyImage(selectedImage, ocrEngine, analysisMode, outputScript);
        setResultType("image");
      } else {
        if (!selectedFile) {
          alert("Please select a file");
          return;
        }
        response = await identifyFile(selectedFile, analysisMode, outputScript);
        setResultType("file");
      }
      
      setResult(response);
    } catch (err) {
      console.error("Analysis failed:", err);
    }
  };

  const handleCloseResults = () => {
    setResult(null);
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
            onClick={() => setActiveTab("text")}
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
            onClick={() => setActiveTab("image")}
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
            onClick={() => setActiveTab("file")}
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
                  onClick={() => imageInputRef.current?.click()}
                  className="group border-2 border-dashed border-[var(--color-border-subtle)] rounded-[20px] p-12 bg-gradient-to-b from-white to-[#fdf8f3] hover:from-white hover:to-[var(--color-primary-soft)] transition-all duration-300 cursor-pointer hover:border-[var(--color-primary)] hover:shadow-xl"
                >
                  {imagePreview ? (
                    <div className="flex flex-col items-center gap-6">
                      <div className="relative">
                        <img 
                          src={imagePreview} 
                          alt="Preview" 
                          className="max-h-56 rounded-xl shadow-lg border-4 border-white"
                        />
                        <div className="absolute -top-2 -right-2 p-2 bg-green-500 rounded-full shadow-md">
                          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                      </div>
                      <div className="text-center">
                        <p className="text-base font-medium text-[var(--color-text-main)] mb-1">
                          {selectedImage?.name}
                        </p>
                        <p className="text-sm text-[var(--color-text-muted)]">
                          Click to change image
                        </p>
                      </div>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedImage(null);
                          setImagePreview(null);
                        }}
                        className="flex items-center gap-2 text-sm text-red-500 hover:text-red-600 font-medium hover:underline px-4 py-2 rounded-full hover:bg-red-50 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Remove Image
                      </button>
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
              
              {/* OCR Engine Selection */}
              <div className="bg-white p-5 rounded-[16px] border border-[var(--color-border-subtle)]">
                <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base">
                  OCR Engine
                </label>
                <div className="relative">
                  <select
                    value={ocrEngine}
                    onChange={(e) => setOcrEngine(e.target.value as OCREngine)}
                    className="w-full h-[52px] rounded-[14px] border-2 border-[var(--color-border-subtle)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-0 focus:shadow-[0_0_0_3px_rgba(255,153,51,0.2)] bg-[#fdf8f3] text-[var(--color-text-main)] appearance-none cursor-pointer transition-all duration-300 hover:border-[var(--color-border-strong)] text-base font-medium px-5"
                  >
                    <option value="tesseract">Tesseract OCR (Free)</option>
                    <option value="google" disabled={!ocrAvailable.google}>
                      Google Cloud Vision {!ocrAvailable.google && '(Not Available)'}
                    </option>
                  </select>
                  <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none bg-[var(--color-primary-soft)] p-1.5 rounded-full">
                    <svg className="w-4 h-4 text-[var(--color-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>
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

        {/* Bottom Action Row */}
        <div className="analysis-row mt-8 pt-6 border-t border-[var(--color-border-subtle)] bg-[#fdf8f3] -mx-8 px-8 py-6 -mb-8 rounded-b-[20px]">
          {/* Analysis Mode */}
          <div className="flex-1 field-group mb-0">
            <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base">
              Analysis Mode
            </label>
            <div className="relative">
              <select
                value={analysisMode}
                onChange={(e) => setAnalysisMode(e.target.value as AnalysisMode)}
                className="w-full h-[52px] rounded-[14px] border-2 border-[var(--color-border-subtle)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-0 focus:shadow-[0_0_0_3px_rgba(255,153,51,0.2)] bg-white text-[var(--color-text-main)] appearance-none cursor-pointer transition-all duration-300 hover:border-[var(--color-border-strong)] text-base font-medium px-5"
              >
                <option value="line">Line by Line</option>
                <option value="verse">Full Verse</option>
              </select>
              <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none bg-[var(--color-primary-soft)] p-1.5 rounded-full">
                <svg className="w-4 h-4 text-[var(--color-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Output Script */}
          <div className="flex-1 field-group mb-0">
            <label className="block text-[var(--color-text-main)] mb-3 font-semibold text-base">
              Output Script
            </label>
            <div className="relative">
              <select
                value={outputScript}
                onChange={(e) => setOutputScript(e.target.value)}
                className="w-full h-[52px] rounded-[14px] border-2 border-[var(--color-border-subtle)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-0 focus:shadow-[0_0_0_3px_rgba(255,153,51,0.2)] bg-white text-[var(--color-text-main)] appearance-none cursor-pointer transition-all duration-300 hover:border-[var(--color-border-strong)] text-base font-medium px-5"
              >
                {schemes.map((scheme) => (
                  <option key={scheme.value} value={scheme.value}>
                    {scheme.label}
                  </option>
                ))}
              </select>
              <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none bg-[var(--color-primary-soft)] p-1.5 rounded-full">
                <svg className="w-4 h-4 text-[var(--color-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Identify Button */}
          <div className="flex-shrink-0 self-end">
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
        </div>

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

      {/* Results Display - SEPARATE container, wider width */}
      {result && (
        <div style={{ width: '1400px', maxWidth: '100%', margin: '40px auto 0 auto' }}>
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