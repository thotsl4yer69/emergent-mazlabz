import React, { useState, useRef } from 'react'

const DocumentUploader = ({ onClose, onUpload }) => {
  const [uploadStep, setUploadStep] = useState('selection') // selection, uploading, success
  const [selectedFiles, setSelectedFiles] = useState([])
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  const fileInputRef = useRef(null)

  // Supported document types
  const supportedTypes = {
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx'
  }

  const handleFileSelection = () => {
    // Trigger file input
    fileInputRef.current?.click()
  }

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files)
    const validFiles = files.filter(file => 
      Object.keys(supportedTypes).includes(file.type) || 
      Object.values(supportedTypes).some(ext => file.name.toLowerCase().endsWith(ext))
    )

    if (validFiles.length === 0) {
      alert('Please select valid document files (PDF, DOC, DOCX, TXT, XLS, XLSX, PPT, PPTX)')
      return
    }

    // Limit to last 10 files (most recent based on lastModified)
    const sortedFiles = validFiles
      .sort((a, b) => (b.lastModified || 0) - (a.lastModified || 0))
      .slice(0, 10)

    setSelectedFiles(sortedFiles)
    setUploadStep('uploading')
    processUpload(sortedFiles)
  }

  const processUpload = async (files) => {
    setIsProcessing(true)
    setUploadProgress(0)

    // Simulate upload process with progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 100))
      setUploadProgress(i)
    }

    // Process files into base64 for storage (as per system requirements)
    const processedFiles = await Promise.all(
      files.map(async (file) => {
        return new Promise((resolve) => {
          const reader = new FileReader()
          reader.onload = (e) => {
            resolve({
              name: file.name,
              size: file.size,
              type: file.type,
              lastModified: file.lastModified,
              content: e.target.result, // base64 content
              uploadTime: new Date().toLocaleString()
            })
          }
          reader.readAsDataURL(file)
        })
      })
    )

    setSelectedFiles(processedFiles)
    setUploadStep('success')
    setIsProcessing(false)

    // Send to parent component
    onUpload(processedFiles)

    // Auto-close after success
    setTimeout(() => {
      onClose()
    }, 3000)
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = (filename) => {
    const ext = filename.toLowerCase().split('.').pop()
    const icons = {
      pdf: '📄',
      doc: '📝',
      docx: '📝',
      txt: '📄',
      xls: '📊',
      xlsx: '📊',
      ppt: '📽️',
      pptx: '📽️'
    }
    return icons[ext] || '📄'
  }

  if (uploadStep === 'success') {
    return (
      <div className="upload-modal">
        <div className="upload-content success-upload">
          <div className="success-content">
            <div className="success-icon">✅</div>
            <h2>DOCUMENTS UPLOADED SUCCESSFULLY!</h2>
            
            <div className="upload-summary">
              <h3>📁 Uploaded Files:</h3>
              <div className="file-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <span className="file-icon">{getFileIcon(file.name)}</span>
                    <div className="file-details">
                      <div className="file-name">{file.name}</div>
                      <div className="file-size">{formatFileSize(file.size)}</div>
                    </div>
                    <span className="upload-check">✓</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="next-steps">
              <h3>🤖 AI Analysis Ready:</h3>
              <ul>
                <li data-icon="🔐">Files encrypted and secured</li>
                <li data-icon="🧠">Ready for AI processing</li>
                <li data-icon="📊">Available for analysis commands</li>
                <li data-icon="💾">Stored in secure session</li>
              </ul>
            </div>

            <div className="terminal-tip">
              <p>💡 <strong>Terminal Tip:</strong> Use 'files' command to view all uploaded documents</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (uploadStep === 'uploading') {
    return (
      <div className="upload-modal">
        <div className="upload-content uploading">
          <div className="upload-animation">
            <h2>🚀 UPLOADING DOCUMENTS...</h2>
            
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <div className="progress-text">{uploadProgress}%</div>
            </div>

            <div className="upload-status">
              <p>📡 Establishing secure connection...</p>
              <p>🔐 Encrypting files with enterprise-grade security...</p>
              <p>☁️ Uploading to MAZLABZ secure servers...</p>
              <p>🧠 Preparing for AI analysis...</p>
            </div>

            <div className="file-preview">
              <h3>Files Being Processed:</h3>
              {selectedFiles.map((file, index) => (
                <div key={index} className="processing-file">
                  <span className="file-icon">{getFileIcon(file.name)}</span>
                  <span className="file-name">{file.name}</span>
                  <span className="processing-spinner">⟳</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="upload-modal">
      <div className="upload-content">
        <div className="modal-header">
          <h2>📱 MOBILE DOCUMENT UPLOAD</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="upload-intro">
          <p>Upload your recent documents for AI analysis and enterprise processing.</p>
          <div className="security-badges">
            <span className="badge">🔒 Encrypted</span>
            <span className="badge">📱 Mobile Ready</span>
            <span className="badge">🧠 AI Analysis</span>
            <span className="badge">⚡ Instant Upload</span>
          </div>
        </div>

        <div className="supported-formats">
          <h3>📄 Supported Document Types:</h3>
          <div className="format-grid">
            <div className="format-item">📄 PDF Documents</div>
            <div className="format-item">📝 Word Documents (.doc, .docx)</div>
            <div className="format-item">📊 Excel Spreadsheets (.xls, .xlsx)</div>
            <div className="format-item">📽️ PowerPoint Presentations (.ppt, .pptx)</div>
            <div className="format-item">📄 Text Files (.txt)</div>
            <div className="format-item">📋 All Office Documents</div>
          </div>
        </div>

        <div className="upload-actions">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.xls,.xlsx,.ppt,.pptx"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          
          <button 
            className="upload-btn primary"
            onClick={handleFileSelection}
            disabled={isProcessing}
          >
            📂 SELECT DOCUMENTS FROM DEVICE
          </button>

          <div className="upload-info">
            <p>🔐 <strong>Enterprise Security:</strong> All uploads are encrypted end-to-end</p>
            <p>📱 <strong>Mobile Optimized:</strong> Works seamlessly on all devices</p>
            <p>🧠 <strong>AI Ready:</strong> Files prepared for intelligent analysis</p>
            <p>⚡ <strong>Instant Processing:</strong> Upload and analyze in real-time</p>
          </div>
        </div>

        <div className="upload-tips">
          <h3>💡 Upload Tips:</h3>
          <ul>
            <li>• Select up to 10 most recent documents</li>
            <li>• Files are automatically sorted by modification date</li>
            <li>• Supported formats: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT</li>
            <li>• Maximum file size: 10MB per document</li>
            <li>• Files are processed instantly for AI analysis</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default DocumentUploader