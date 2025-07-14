#!/usr/bin/env python3
"""
Comprehensive Backend Testing for MAZLABZ File Upload System
Tests all FastAPI endpoints with various scenarios
"""

import requests
import json
import os
import tempfile
from pathlib import Path
import time
import sys

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.test_results = []
        self.uploaded_file_ids = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def create_test_file(self, filename, content, size_mb=None):
        """Create a test file for upload testing"""
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        if size_mb:
            # Create file of specific size
            content = b'A' * (size_mb * 1024 * 1024)
        elif isinstance(content, str):
            content = content.encode('utf-8')
            
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    
    def test_health_check(self):
        """Test GET /api/health endpoint"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy" and data.get("database") == "connected":
                    self.log_result("Health Check", True, "Server and database are healthy")
                else:
                    self.log_result("Health Check", False, "Health check returned unexpected data", data)
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}", response.text)
                
        except requests.exceptions.RequestException as e:
            self.log_result("Health Check", False, f"Connection error: {str(e)}")
    
    def test_file_upload_valid(self):
        """Test POST /api/upload with valid files"""
        try:
            # Test with different file types
            test_files = [
                ("test_image.jpg", b"fake_jpeg_content", "image/jpeg"),
                ("test_document.pdf", b"fake_pdf_content", "application/pdf"),
                ("test_text.txt", "Hello, this is a test document for MAZLABZ upload system!", "text/plain")
            ]
            
            for filename, content, content_type in test_files:
                file_path = self.create_test_file(filename, content)
                
                with open(file_path, 'rb') as f:
                    files = {'files': (filename, f, content_type)}
                    response = requests.post(f"{API_BASE}/upload", files=files, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("files") and len(data["files"]) > 0:
                        file_id = data["files"][0]["id"]
                        self.uploaded_file_ids.append(file_id)
                        self.log_result(f"File Upload - {filename}", True, f"Successfully uploaded {filename}")
                    else:
                        self.log_result(f"File Upload - {filename}", False, "No file data in response", data)
                else:
                    self.log_result(f"File Upload - {filename}", False, f"HTTP {response.status_code}", response.text)
                
                # Clean up temp file
                os.remove(file_path)
                
        except Exception as e:
            self.log_result("File Upload - Valid Files", False, f"Exception: {str(e)}")
    
    def test_file_upload_invalid_type(self):
        """Test POST /api/upload with invalid file types"""
        try:
            # Test with disallowed file type
            file_path = self.create_test_file("test_script.exe", b"fake_executable_content")
            
            with open(file_path, 'rb') as f:
                files = {'files': ("test_script.exe", f, "application/octet-stream")}
                response = requests.post(f"{API_BASE}/upload", files=files, timeout=30)
            
            if response.status_code == 400:
                self.log_result("File Upload - Invalid Type", True, "Correctly rejected invalid file type")
            else:
                self.log_result("File Upload - Invalid Type", False, f"Should reject invalid file type, got HTTP {response.status_code}")
            
            os.remove(file_path)
            
        except Exception as e:
            self.log_result("File Upload - Invalid Type", False, f"Exception: {str(e)}")
    
    def test_file_upload_large_file(self):
        """Test POST /api/upload with file exceeding size limit"""
        try:
            # Create file larger than 10MB
            file_path = self.create_test_file("large_file.txt", None, size_mb=11)
            
            with open(file_path, 'rb') as f:
                files = {'files': ("large_file.txt", f, "text/plain")}
                response = requests.post(f"{API_BASE}/upload", files=files, timeout=60)
            
            if response.status_code == 400:
                self.log_result("File Upload - Size Limit", True, "Correctly rejected oversized file")
            else:
                self.log_result("File Upload - Size Limit", False, f"Should reject large file, got HTTP {response.status_code}")
            
            os.remove(file_path)
            
        except Exception as e:
            self.log_result("File Upload - Size Limit", False, f"Exception: {str(e)}")
    
    def test_file_listing(self):
        """Test GET /api/files endpoint"""
        try:
            response = requests.get(f"{API_BASE}/files", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "files" in data and isinstance(data["files"], list):
                    file_count = len(data["files"])
                    self.log_result("File Listing", True, f"Retrieved {file_count} files successfully")
                    
                    # Verify file structure
                    if file_count > 0:
                        sample_file = data["files"][0]
                        required_fields = ["id", "filename", "size", "content_type", "upload_date"]
                        missing_fields = [field for field in required_fields if field not in sample_file]
                        
                        if not missing_fields:
                            self.log_result("File Listing - Structure", True, "File metadata structure is correct")
                        else:
                            self.log_result("File Listing - Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("File Listing", False, "Response missing 'files' array", data)
            else:
                self.log_result("File Listing", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("File Listing", False, f"Exception: {str(e)}")
    
    def test_dashboard(self):
        """Test GET /api/dashboard endpoint"""
        try:
            response = requests.get(f"{API_BASE}/dashboard", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_files", "total_size", "files"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    total_files = data["total_files"]
                    total_size = data["total_size"]
                    files_count = len(data["files"])
                    
                    self.log_result("Dashboard", True, 
                                  f"Dashboard data: {total_files} total files, {total_size} bytes, {files_count} recent files")
                else:
                    self.log_result("Dashboard", False, f"Missing fields: {missing_fields}", data)
            else:
                self.log_result("Dashboard", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Dashboard", False, f"Exception: {str(e)}")
    
    def test_file_download(self):
        """Test GET /api/files/{file_id} endpoint"""
        if not self.uploaded_file_ids:
            self.log_result("File Download", False, "No uploaded files to test download")
            return
            
        try:
            file_id = self.uploaded_file_ids[0]
            response = requests.get(f"{API_BASE}/files/{file_id}", timeout=10)
            
            if response.status_code == 200:
                # Check if we got file content
                content_length = len(response.content)
                content_type = response.headers.get('content-type', 'unknown')
                
                self.log_result("File Download", True, 
                              f"Successfully downloaded file ({content_length} bytes, {content_type})")
            else:
                self.log_result("File Download", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("File Download", False, f"Exception: {str(e)}")
    
    def test_file_download_nonexistent(self):
        """Test GET /api/files/{file_id} with non-existent file"""
        try:
            fake_id = "nonexistent-file-id-12345"
            response = requests.get(f"{API_BASE}/files/{fake_id}", timeout=10)
            
            if response.status_code == 404:
                self.log_result("File Download - Not Found", True, "Correctly returned 404 for non-existent file")
            else:
                self.log_result("File Download - Not Found", False, f"Should return 404, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("File Download - Not Found", False, f"Exception: {str(e)}")
    
    def test_root_endpoint(self):
        """Test GET / root endpoint"""
        try:
            response = requests.get(BACKEND_URL, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "MAZLABZ" in data["message"]:
                    self.log_result("Root Endpoint", True, "Root endpoint responding correctly")
                else:
                    self.log_result("Root Endpoint", False, "Unexpected root response", data)
            else:
                self.log_result("Root Endpoint", False, f"HTTP {response.status_code}", response.text)
                
        except Exception as e:
            self.log_result("Root Endpoint", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("MAZLABZ Backend API Testing")
        print("=" * 60)
        
        # Test server connectivity first
        self.test_root_endpoint()
        self.test_health_check()
        
        # Test file operations
        self.test_file_upload_valid()
        self.test_file_upload_invalid_type()
        self.test_file_upload_large_file()
        
        # Test data retrieval
        self.test_file_listing()
        self.test_dashboard()
        
        # Test file download
        self.test_file_download()
        self.test_file_download_nonexistent()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)