import { useCallback, useState } from 'react';
import { UploadCloud, X } from 'lucide-react';
import { cn } from '../utils';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  isLoading: boolean;
}

export function UploadZone({ onFileSelect, isLoading }: UploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateAndSelectFile = useCallback((file: File) => {
    setError(null);
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
    
    if (!validTypes.includes(file.type)) {
      setError('Invalid file type. Please upload a JPEG, PNG, or PDF.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File is too large. Maximum size is 10MB.');
      return;
    }

    onFileSelect(file);
  }, [onFileSelect]);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isLoading) setIsDragActive(true);
  }, [isLoading]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (isLoading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  }, [isLoading, validateAndSelectFile]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelectFile(e.target.files[0]);
    }
  }, [validateAndSelectFile]);

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative group flex flex-col items-center justify-center w-full h-64 p-6 border-2 border-dashed rounded-2xl transition-all duration-200 ease-in-out",
          isDragActive 
            ? "border-blue-500 bg-blue-50/50 scale-[1.02]" 
            : "border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50",
          isLoading && "opacity-50 cursor-not-allowed pointer-events-none"
        )}
      >
        <input
          type="file"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          onChange={handleFileChange}
          accept=".jpg,.jpeg,.png,.pdf"
          disabled={isLoading}
        />
        
        <div className="flex flex-col items-center space-y-4 text-center pointer-events-none">
          <div className={cn(
            "p-4 rounded-full transition-colors duration-200",
            isDragActive ? "bg-blue-100 text-blue-600" : "bg-slate-100 text-slate-500 group-hover:bg-slate-200"
          )}>
            <UploadCloud className="w-8 h-8" strokeWidth={1.5} />
          </div>
          
          <div className="space-y-1">
            <p className="text-lg font-medium text-slate-700">
              Drag & drop a document here
            </p>
            <p className="text-sm text-slate-500">
              or click to browse from your computer
            </p>
          </div>
          
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
            <span>Supports: JPG, PNG, PDF</span>
            <span>•</span>
            <span>Max: 10MB</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-600 rounded-lg flex items-start gap-2 text-sm border border-red-100 shadow-sm animate-in fade-in slide-in-from-top-2">
          <X className="w-5 h-5 shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
