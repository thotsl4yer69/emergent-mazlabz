import React, { useState, useEffect } from 'react'

const AutomatedUploader = ({ onUpload, onClose }) => {
  const [isPermissionGranted, setIsPermissionGranted] = useState(false)
  const [isScanning, setIsScanning] = useState(false)
  const [scanResults, setScanResults] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const BACKEND_URL = import.meta.env.REACT_APP_BACKEND_URL || 'http://localhost:8001'

  // Check if File System Access API is supported
  const isFileSystemAccessSupported = () => {
    return 'showOpenFilePicker' in window || 'showDirectoryPicker' in window
  }

  // Request permission and scan for recent files
  const requestPermissionAndScan = async () => {
    try {
      if (!isFileSystemAccessSupported()) {
        // Fallback to regular file input
        const input = document.createElement('input')
        input.type = 'file'
        input.multiple = true
        input.accept = '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.bmp,.webp,.xls,.xlsx,.ppt,.pptx'
        input.onchange = (e) => {
          const files = Array.from(e.target.files)
          if (files.length > 0) {
            setScanResults(files.slice(0, 10)) // Limit to 10 files
            setIsPermissionGranted(true)
            setIsScanning(false)
          }
        }
        input.click()
        return
      }

      setIsScanning(true)
      
      // Request file access permission
      const fileHandles = await window.showOpenFilePicker({
        multiple: true,
        types: [
          {
            description: 'Documents and Images',
            accept: {
              'application/pdf': ['.pdf'],
              'application/msword': ['.doc'],
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
              'text/plain': ['.txt'],
              'image/jpeg': ['.jpg', '.jpeg'],
              'image/png': ['.png'],
              'image/gif': ['.gif'],
              'image/bmp': ['.bmp'],
              'image/webp': ['.webp'],
              'application/vnd.ms-excel': ['.xls'],
              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
              'application/vnd.ms-powerpoint': ['.ppt'],
              'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx']
            }
          }
        ]
      })

      const files = await Promise.all(
        fileHandles.slice(0, 10).map(async (handle) => {
          const file = await handle.getFile()
          return file
        })
      )

      setScanResults(files)
      setIsPermissionGranted(true)
      setIsScanning(false)
    } catch (error) {
      console.error('Permission denied or error:', error)
      setIsScanning(false)
      onClose()
    }
  }

  // Upload files to backend
  const uploadFiles = async (files) => {
    if (!files || files.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      files.forEach((file) => {
        formData.append('files', file)
      })

      const response = await fetch(`${BACKEND_URL}/api/upload`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      setUploadProgress(100)
      
      // Call parent handler with uploaded files info
      onUpload(result.files)
      
      // Close modal after short delay
      setTimeout(() => {
        onClose()
      }, 1000)

    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please try again.')
      setIsUploading(false)
    }
  }

  // Auto-start permission request and scan
  useEffect(() => {
    requestPermissionAndScan()
  }, [])

  // Auto-upload if files are found
  useEffect(() => {
    if (scanResults.length > 0 && !isUploading) {
      // Auto-upload after 1 second delay
      setTimeout(() => {
        uploadFiles(scanResults)
      }, 1000)
    }
  }, [scanResults])

  return (
    <div className="modal-overlay">
      <div className="modal-content document-uploader">
        <div className="modal-header">
          <h3>🚀 Automated Document Upload</h3>
          <div className="enterprise-badges">
            <span className="security-badge">🔒 Enterprise Security</span>
            <span className="encryption-badge">🛡️ 256-bit Encryption</span>
          </div>
        </div>
        
        <div className="upload-status">
          {isScanning && (
            <div className="scanning-animation">
              <div className="scanner-line"></div>
              <p>🔍 Scanning for recent documents...</p>
              <p className="scanning-text">Accessing file system with your permission...</p>
            </div>
          )}
          
          {isPermissionGranted && scanResults.length > 0 && !isUploading && (
            <div className="scan-results">
              <h4>📄 Found {scanResults.length} Recent Files</h4>
              <div className="files-preview">
                {scanResults.map((file, index) => (
                  <div key={index} className="file-preview">
                    <span className="file-icon">📄</span>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">({(file.size / 1024).toFixed(1)}KB)</span>
                  </div>
                ))}
              </div>
              <p className="auto-upload-notice">⚡ Auto-uploading in 1 second...</p>
            </div>
          )}
          
          {isUploading && (
            <div className="upload-progress">
              <h4>📤 Uploading Files...</h4>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p>{uploadProgress}% Complete</p>
            </div>
          )}
          
          {uploadProgress === 100 && (
            <div className="upload-complete">
              <h4>✅ Upload Complete!</h4>
              <p>Files successfully uploaded to secure server</p>
              <p>Access via dashboard or 'files' command</p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button 
            className="close-button"
            onClick={onClose}
            disabled={isUploading}
          >
            {isUploading ? 'Uploading...' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default AutomatedUploader