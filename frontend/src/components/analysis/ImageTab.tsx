import { Image } from "lucide-react";
import type { ImageInput } from "../../hooks/useImageInput";
import {
  ChooseFileButton,
  ClearButton,
  DropZoneFrame,
  EmptyDropPrompt,
  ExtractButton,
  ExtractedTextBody,
  ExtractedTextPanel,
  FieldLabel,
  HiddenFileInput,
  IdentifyChandasButton,
  RemoveBadge,
} from "./UploadParts";

interface ImageTabProps {
  input: ImageInput;
  identifying: boolean;
  onIdentify: () => void;
}

/** Image OCR tab: upload a photo of a verse, extract its text, then identify the meter. */
export function ImageTab({ input, identifying, onIdentify }: ImageTabProps) {
  const { image, preview, extractedText, dropZone } = input;

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel>Upload Image for OCR</FieldLabel>
        <HiddenFileInput inputRef={input.inputRef} accept="image/*" onChange={input.onInputChange} />
        <DropZoneFrame
          isDragging={dropZone.isDragging}
          hasSelection={Boolean(image)}
          onClick={() => !image && input.inputRef.current?.click()}
          handlers={dropZone.handlers}
        >
          {preview ? (
            <div className="flex flex-col items-center gap-6">
              <div className="relative">
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-56 rounded-xl shadow-lg border-4 border-white"
                />
                <RemoveBadge title="Remove image" onRemove={input.remove} />
              </div>
              <div className="text-center">
                <p className="text-base font-medium text-[var(--color-text-main)] mb-1">
                  {image?.name}
                </p>
              </div>
              {!extractedText && (
                <ExtractButton loading={input.loading} loadingLabel="Extracting..." onExtract={input.extract} />
              )}
              {extractedText && <ClearButton label="Clear Image" onClear={input.remove} />}
            </div>
          ) : (
            <EmptyDropPrompt
              icon={<Image className="w-10 h-10 text-white" />}
              isDragging={dropZone.isDragging}
              title={dropZone.isDragging ? 'Drop your image here!' : 'Drop your image here'}
              description="or click to browse"
              formats="Supports PNG, JPG, JPEG (max 10MB)"
            >
              <ChooseFileButton isDragging={dropZone.isDragging} />
            </EmptyDropPrompt>
          )}
        </DropZoneFrame>
      </div>

      {extractedText && (
        <ExtractedTextPanel>
          <h3 className="text-2xl font-bold text-[var(--color-text-main)] mb-6">
            Extracted Text
          </h3>
          <ExtractedTextBody text={extractedText} />
          <div className="flex items-center gap-4">
            <IdentifyChandasButton loading={identifying} onIdentify={onIdentify} />
          </div>
        </ExtractedTextPanel>
      )}
    </div>
  );
}
