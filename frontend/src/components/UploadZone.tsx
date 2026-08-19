import { useCallback, useState } from 'react';
import { UploadCloud, X } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { cn } from '../utils';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  isLoading: boolean;
}

export function UploadZone({ onFileSelect, isLoading }: UploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);

  const validateAndSelectFile = useCallback((file: File) => {
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];

    if (!validTypes.includes(file.type)) {
      toast.error('Invalid file type. Please upload a JPEG, PNG, or PDF.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('File is too large. Maximum size is 10MB.');
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
      <motion.div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        animate={isDragActive ? { scale: 1.02 } : { scale: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        className={cn(
          "relative group flex flex-col items-center justify-center w-full h-64 p-6 border-2 border-dashed rounded-2xl transition-colors duration-300 ease-in-out",
          isDragActive
            ? "border-blue-500 bg-blue-500/10 dark:bg-blue-500/20 shadow-[0_0_30px_-5px_rgba(59,130,246,0.3)]"
            : "border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-slate-400 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800",
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
          <motion.div
            animate={{ scale: isDragActive ? 1.2 : 1 }}
            transition={{ type: "spring", stiffness: 400, damping: 10 }}
            className={cn(
              "p-4 rounded-full transition-colors duration-300",
              isDragActive ? "bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400" : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400 group-hover:bg-slate-200 dark:group-hover:bg-slate-700"
            )}>
            <UploadCloud className="w-8 h-8" strokeWidth={1.5} />
          </motion.div>

          <div className="space-y-1">
            <p className="text-lg font-medium text-slate-700 dark:text-slate-200">
              Drag & drop a document here
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              or click to browse from your computer
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            <span>Supports: JPG, PNG, PDF</span>
            <span>•</span>
            <span>Max: 10MB</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
