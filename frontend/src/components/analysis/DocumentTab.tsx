import { AlertTriangle, Upload } from "lucide-react";
import type { DocumentInput } from "../../hooks/useDocumentInput";
import { documentIcon, documentTypeLabel, formatKilobytes } from "./inputFiles";
import {
  ChooseFileButton,
  ClearButton,
  DropZoneFrame,
  EmptyDropPrompt,
  ErrorCallout,
  ExtractButton,
  ExtractedTextBody,
  ExtractedTextPanel,
  FieldLabel,
  HiddenFileInput,
  IdentifyChandasButton,
  SelectedFileSummary,
} from "./UploadParts";

interface DocumentTabProps {
  input: DocumentInput;
  identifying: boolean;
  onIdentify: () => void;
}

const BADGE = "px-3 py-1 bg-white rounded-full border border-[var(--color-border-subtle)]";

/** File Upload tab: upload a DOCX or TXT file, extract its text, then identify the meter. */
export function DocumentTab({ input, identifying, onIdentify }: DocumentTabProps) {
  const { file, extractedText, fileInfo, warnings, dropZone } = input;

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel>Upload Document File</FieldLabel>
        <HiddenFileInput inputRef={input.inputRef} accept=".docx,.txt,.text" onChange={input.onInputChange} />
        <DropZoneFrame
          isDragging={dropZone.isDragging}
          hasSelection={Boolean(file)}
          onClick={() => !file && input.inputRef.current?.click()}
          handlers={dropZone.handlers}
        >
          {file ? (
            <div className="flex flex-col items-center gap-6">
              <SelectedFileSummary
                icon={documentIcon(file.name)}
                name={file.name}
                size={formatKilobytes(file.size)}
                removeTitle="Remove file"
                onRemove={input.remove}
              />
              {!extractedText && (
                <ExtractButton loading={input.loading} loadingLabel="Extracting..." onExtract={input.extract} />
              )}
              {extractedText && <ClearButton label="Clear File" onClear={input.remove} />}
            </div>
          ) : (
            <EmptyDropPrompt
              icon={<Upload className="w-10 h-10 text-white" />}
              isDragging={dropZone.isDragging}
              title={dropZone.isDragging ? 'Drop your file here!' : 'Drop your file here'}
              description="or click to browse"
              formats="Supports DOCX, TXT (max 10MB)"
            >
              <ChooseFileButton isDragging={dropZone.isDragging} />
            </EmptyDropPrompt>
          )}
        </DropZoneFrame>
      </div>

      {input.error && (
        <ErrorCallout title="Extraction Failed" message={input.error} details={input.errorDetails} />
      )}

      {extractedText && (
        <ExtractedTextPanel>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-[var(--color-text-main)]">
              Extracted Text
            </h3>
            {fileInfo && (
              <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
                <span className={BADGE}>{documentTypeLabel(fileInfo.file_type)}</span>
                {fileInfo.page_count > 1 && <span className={BADGE}>{fileInfo.page_count} pages</span>}
              </div>
            )}
          </div>

          {warnings.length > 0 && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-[12px] flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-amber-700">Extraction Warning</p>
                {warnings.map((warning, idx) => (
                  <p key={idx} className="text-sm text-amber-600 mt-1">{warning}</p>
                ))}
              </div>
            </div>
          )}

          <ExtractedTextBody text={extractedText} scrollable />
          <div className="flex items-center gap-4">
            <IdentifyChandasButton loading={identifying} onIdentify={onIdentify} />
          </div>
        </ExtractedTextPanel>
      )}
    </div>
  );
}
