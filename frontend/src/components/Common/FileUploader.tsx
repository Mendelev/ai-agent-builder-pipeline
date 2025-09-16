import React, { useCallback } from 'react';
import { Upload, X } from 'lucide-react';
import clsx from 'clsx';

interface FileUploaderProps {
  onUpload: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  className?: string;
  label?: string;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onUpload,
  accept = '*',
  multiple = false,
  className,
  label = 'Upload files',
}) => {
  const [dragActive, setDragActive] = React.useState(false);
  const [files, setFiles] = React.useState<File[]>([]);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        const newFiles = Array.from(e.dataTransfer.files);
        setFiles(newFiles);
        onUpload(newFiles);
      }
    },
    [onUpload]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files[0]) {
        const newFiles = Array.from(e.target.files);
        setFiles(newFiles);
        onUpload(newFiles);
      }
    },
    [onUpload]
  );

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    if (newFiles.length === 0 && inputRef.current) {
      inputRef.current.value = '';
    }
  };

  return (
    <div className={className}>
      <div
        className={clsx(
          'relative border-2 border-dashed rounded-lg p-6 text-center',
          dragActive
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          multiple={multiple}
          accept={accept}
          onChange={handleChange}
        />
        
        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="font-medium text-blue-600 hover:text-blue-500"
          >
            {label}
          </button>
          {' or drag and drop'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {accept === '*' ? 'Any file type' : accept}
        </p>
      </div>

      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((file, index) => (
            <li
              key={index}
              className="flex items-center justify-between p-2 bg-gray-50 rounded"
            >
              <span className="text-sm text-gray-600">{file.name}</span>
              <button
                onClick={() => removeFile(index)}
                className="text-red-500 hover:text-red-700"
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};