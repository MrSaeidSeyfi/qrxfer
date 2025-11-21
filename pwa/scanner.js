class QRScanner {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.stream = null;
        this.scanning = false;
        this.chunks = new Map(); // chunk_index -> chunk_data
        this.totalChunks = null;
        this.lastScanTime = 0;
        this.scanInterval = 100; // Scan every 100ms
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('startBtn').addEventListener('click', () => this.start());
        document.getElementById('stopBtn').addEventListener('click', () => this.stop());
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadFile());
    }

    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 1280 }
                }
            });
            
            this.video.srcObject = this.stream;
            this.video.play();
            
            this.scanning = true;
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            
            this.updateStatus('Camera started. Scanning for QR codes...', 'info');
            this.scan();
        } catch (error) {
            this.updateStatus(`Error accessing camera: ${error.message}`, 'error');
            console.error('Camera error:', error);
        }
    }

    stop() {
        this.scanning = false;
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        this.video.srcObject = null;
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        this.updateStatus('Camera stopped', 'info');
    }

    scan() {
        if (!this.scanning) return;

        const now = Date.now();
        if (now - this.lastScanTime < this.scanInterval) {
            requestAnimationFrame(() => this.scan());
            return;
        }
        this.lastScanTime = now;

        if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            this.detectAndDecodeQR(imageData);
        }

        requestAnimationFrame(() => this.scan());
    }

    detectAndDecodeQR(imageData) {
        // First, try to detect green border and extract QR region
        const qrRegion = this.detectGreenBorder(imageData);
        
        if (qrRegion) {
            // Extract the QR code region
            const qrImageData = this.ctx.getImageData(
                qrRegion.x, qrRegion.y, qrRegion.width, qrRegion.height
            );
            
            // Try to decode QR code
            const code = jsQR(qrImageData.data, qrImageData.width, qrImageData.height);
            
            if (code) {
                this.processQRCode(code);
            }
        } else {
            // Fallback: try to decode entire frame (in case border detection fails)
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            if (code) {
                this.processQRCode(code);
            }
        }
    }

    detectGreenBorder(imageData) {
        const width = imageData.width;
        const height = imageData.height;
        const data = imageData.data;
        const borderThreshold = 20; // pixels from edge to check
        const greenThreshold = 100; // minimum green value
        const minBorderRatio = 0.3; // minimum ratio of green pixels in border area
        
        // Check top border
        let topGreenCount = 0;
        let topTotal = 0;
        for (let y = 0; y < borderThreshold && y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = (y * width + x) * 4;
                const r = data[idx];
                const g = data[idx + 1];
                const b = data[idx + 2];
                topTotal++;
                if (g > greenThreshold && g > r * 1.5 && g > b * 1.5) {
                    topGreenCount++;
                }
            }
        }
        
        // Check bottom border
        let bottomGreenCount = 0;
        let bottomTotal = 0;
        for (let y = Math.max(0, height - borderThreshold); y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = (y * width + x) * 4;
                const r = data[idx];
                const g = data[idx + 1];
                const b = data[idx + 2];
                bottomTotal++;
                if (g > greenThreshold && g > r * 1.5 && g > b * 1.5) {
                    bottomGreenCount++;
                }
            }
        }
        
        // Check left border
        let leftGreenCount = 0;
        let leftTotal = 0;
        for (let x = 0; x < borderThreshold && x < width; x++) {
            for (let y = 0; y < height; y++) {
                const idx = (y * width + x) * 4;
                const r = data[idx];
                const g = data[idx + 1];
                const b = data[idx + 2];
                leftTotal++;
                if (g > greenThreshold && g > r * 1.5 && g > b * 1.5) {
                    leftGreenCount++;
                }
            }
        }
        
        // Check right border
        let rightGreenCount = 0;
        let rightTotal = 0;
        for (let x = Math.max(0, width - borderThreshold); x < width; x++) {
            for (let y = 0; y < height; y++) {
                const idx = (y * width + x) * 4;
                const r = data[idx];
                const g = data[idx + 1];
                const b = data[idx + 2];
                rightTotal++;
                if (g > greenThreshold && g > r * 1.5 && g > b * 1.5) {
                    rightGreenCount++;
                }
            }
        }
        
        const topRatio = topGreenCount / topTotal;
        const bottomRatio = bottomGreenCount / bottomTotal;
        const leftRatio = leftGreenCount / leftTotal;
        const rightRatio = rightGreenCount / rightTotal;
        
        // If we have green borders on all sides, extract the inner region
        if (topRatio > minBorderRatio && bottomRatio > minBorderRatio && 
            leftRatio > minBorderRatio && rightRatio > minBorderRatio) {
            
            // Estimate border width (average of detected borders)
            const borderWidth = Math.max(5, Math.min(
                Math.floor((topGreenCount + bottomGreenCount + leftGreenCount + rightGreenCount) / (topTotal + bottomTotal + leftTotal + rightTotal) * borderThreshold),
                20
            ));
            
            return {
                x: borderWidth,
                y: borderWidth,
                width: width - (borderWidth * 2),
                height: height - (borderWidth * 2)
            };
        }
        
        return null;
    }

    async processQRCode(qrCode) {
        try {
            // jsQR returns binary data in binaryData property for byte mode QR codes
            let bytes;
            if (qrCode.binaryData) {
                // Binary mode QR code
                bytes = new Uint8Array(qrCode.binaryData);
            } else if (qrCode.data) {
                if (typeof qrCode.data === 'string') {
                    // Try to decode as base64 first (common for binary data in text mode)
                    try {
                        bytes = this.base64ToBytes(qrCode.data);
                    } catch (e) {
                        // If not base64, try to parse as hex or encode as UTF-8
                        // For now, encode as UTF-8 (this might not work for binary data)
                        bytes = new TextEncoder().encode(qrCode.data);
                    }
                } else if (qrCode.data instanceof Uint8Array) {
                    bytes = qrCode.data;
                } else if (Array.isArray(qrCode.data)) {
                    bytes = new Uint8Array(qrCode.data);
                } else {
                    console.warn('Unknown QR code data format:', typeof qrCode.data);
                    return;
                }
            } else {
                console.warn('No data found in QR code');
                return;
            }
            
            if (bytes.length < 12) {
                console.warn(`QR code data too small: ${bytes.length} bytes`);
                return; // Too small to be a valid chunk
            }
            
            // Parse header: total_chunks (4 bytes) + chunk_index (4 bytes)
            const totalChunks = this.readUint32(bytes, 0);
            const chunkIndex = this.readUint32(bytes, 4);
            const chunkData = bytes.slice(8, bytes.length - 4);
            const crc = this.readUint32(bytes, bytes.length - 4);
            
            // Verify CRC
            const calculatedCrc = this.crc32(chunkData) & 0xffffffff;
            if (calculatedCrc !== crc) {
                console.warn(`CRC mismatch for chunk ${chunkIndex}: expected ${crc}, got ${calculatedCrc}`);
                return;
            }
            
            // Store chunk
            if (!this.chunks.has(chunkIndex)) {
                // Create a copy of the chunk data to store
                const chunkCopy = new Uint8Array(chunkData);
                this.chunks.set(chunkIndex, chunkCopy);
                
                if (this.totalChunks === null) {
                    this.totalChunks = totalChunks;
                    console.log(`Detected total chunks: ${totalChunks}`);
                }
                
                console.log(`Scanned chunk ${chunkIndex + 1}/${totalChunks}`);
                this.updateUI();
                
                // Check if we have all chunks
                if (this.chunks.size === this.totalChunks) {
                    this.reconstructFile();
                }
            }
        } catch (error) {
            console.error('Error processing QR code:', error);
        }
    }

    base64ToBytes(base64) {
        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes;
    }

    readUint32(bytes, offset) {
        return bytes[offset] | 
               (bytes[offset + 1] << 8) | 
               (bytes[offset + 2] << 16) | 
               (bytes[offset + 3] << 24);
    }

    crc32(data) {
        // Simple CRC32 implementation (same as zlib.crc32)
        let crc = 0xffffffff;
        const table = [];
        
        // Generate CRC table
        for (let i = 0; i < 256; i++) {
            let c = i;
            for (let j = 0; j < 8; j++) {
                c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
            }
            table[i] = c;
        }
        
        // Calculate CRC
        for (let i = 0; i < data.length; i++) {
            crc = table[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
        }
        
        return (crc ^ 0xffffffff) >>> 0;
    }

    updateUI() {
        const scanned = this.chunks.size;
        const total = this.totalChunks || 0;
        
        document.getElementById('chunksScanned').textContent = scanned;
        document.getElementById('totalChunks').textContent = total > 0 ? total : '-';
        
        const progress = total > 0 ? (scanned / total) * 100 : 0;
        document.getElementById('progressFill').style.width = `${progress}%`;
        
        // Update chunks list
        const chunksList = document.getElementById('chunksList');
        chunksList.innerHTML = '';
        
        if (total > 0) {
            for (let i = 0; i < total; i++) {
                const badge = document.createElement('div');
                badge.className = 'chunk-badge';
                if (this.chunks.has(i)) {
                    badge.textContent = i;
                } else {
                    badge.textContent = i;
                    badge.classList.add('missing');
                }
                chunksList.appendChild(badge);
            }
        }
        
        if (scanned === total && total > 0) {
            this.updateStatus(`All ${total} chunks scanned! Reconstructing file...`, 'success');
        } else if (total > 0) {
            this.updateStatus(`Scanning... ${scanned}/${total} chunks`, 'info');
        } else {
            this.updateStatus('Scanning for QR codes...', 'info');
        }
    }

    async reconstructFile() {
        try {
            this.updateStatus('Reconstructing file from chunks...', 'info');
            
            // Sort chunks by index
            const sortedChunks = [];
            for (let i = 0; i < this.totalChunks; i++) {
                if (!this.chunks.has(i)) {
                    throw new Error(`Missing chunk ${i}`);
                }
                sortedChunks.push(this.chunks.get(i));
            }
            
            // Combine chunks
            const totalLength = sortedChunks.reduce((sum, chunk) => sum + chunk.length, 0);
            const combinedData = new Uint8Array(totalLength);
            let offset = 0;
            for (const chunk of sortedChunks) {
                combinedData.set(chunk, offset);
                offset += chunk.length;
            }
            
            // Decompress using pako (zlib)
            this.updateStatus('Decompressing data...', 'info');
            const decompressed = pako.inflate(combinedData);
            
            // Extract ZIP file
            this.updateStatus('Extracting ZIP file...', 'info');
            const zip = await JSZip.loadAsync(decompressed);
            
            // Get the first file from ZIP
            const fileNames = Object.keys(zip.files);
            if (fileNames.length === 0) {
                throw new Error('No files found in ZIP');
            }
            
            const fileName = fileNames[0];
            const fileData = await zip.files[fileName].async('uint8array');
            
            // Store for download
            this.reconstructedFile = {
                name: fileName,
                data: fileData,
                blob: new Blob([fileData])
            };
            
            // Show result
            document.getElementById('fileInfo').innerHTML = `
                <strong>File:</strong> ${fileName}<br>
                <strong>Size:</strong> ${(fileData.length / 1024).toFixed(2)} KB
            `;
            document.getElementById('resultSection').style.display = 'block';
            this.updateStatus(`File reconstructed successfully: ${fileName}`, 'success');
            
            // Stop scanning
            this.stop();
            
        } catch (error) {
            this.updateStatus(`Error reconstructing file: ${error.message}`, 'error');
            console.error('Reconstruction error:', error);
        }
    }

    downloadFile() {
        if (!this.reconstructedFile) {
            return;
        }
        
        const url = URL.createObjectURL(this.reconstructedFile.blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.reconstructedFile.name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    updateStatus(message, type = 'info') {
        const statusText = document.getElementById('statusText');
        statusText.textContent = message;
        statusText.className = `status-text ${type}`;
    }
}

// Initialize scanner when page loads
let scanner;
window.addEventListener('DOMContentLoaded', () => {
    scanner = new QRScanner();
});

