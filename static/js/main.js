document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const processButton = document.getElementById('processButton');
    const processingStatus = document.getElementById('processingStatus');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('audioFile');
        const file = fileInput.files[0];
        
        if (!file) {
            showError('Please select a file');
            return;
        }

        // Validate file type
        const validTypes = ['audio/mpeg', 'audio/wav', 'audio/x-wav'];
        if (!validTypes.includes(file.type)) {
            showError('Invalid file type. Please upload an MP3 or WAV file.');
            return;
        }

        // Show processing status
        showProcessing(true);
        hideSuccess();
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Processing failed');
            }

            // Get filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            const filenameMatch = contentDisposition ? contentDisposition.match(/filename="(.+)"/) : null;
            const filename = filenameMatch ? filenameMatch[1] : 'processed_audio.mp3';

            // Get the processed file
            const blob = await response.blob();
            
            // Create download URL
            const url = window.URL.createObjectURL(blob);
            
            // Create and configure download link
            const downloadLink = document.createElement('a');
            downloadLink.style.display = 'none';
            downloadLink.href = url;
            downloadLink.download = filename;
            
            // Append, click, and cleanup
            document.body.appendChild(downloadLink);
            downloadLink.click();
            
            // Cleanup
            setTimeout(() => {
                window.URL.revokeObjectURL(url);
                document.body.removeChild(downloadLink);
            }, 100);
            
            // Show success message with filename
            showSuccess(`Processing complete! Your file "${filename}" has been processed and downloaded.`);
            
            // Reset form
            form.reset();
            
        } catch (error) {
            console.error('Processing error:', error);
            let errorMessage = 'An error occurred while processing the audio file.';
            
            // Try to parse detailed error message from response
            if (error.message) {
                try {
                    const errorData = JSON.parse(error.message);
                    errorMessage = errorData.error || error.message;
                } catch (e) {
                    errorMessage = error.message;
                }
            }
            
            showError(`Processing failed: ${errorMessage}`);
        } finally {
            showProcessing(false);
        }
    });

    function showProcessing(show) {
        processingStatus.classList.toggle('d-none', !show);
        processButton.disabled = show;
        errorMessage.classList.add('d-none');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('d-none');
        successMessage.classList.add('d-none');
    }

    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.classList.remove('d-none');
        errorMessage.classList.add('d-none');
    }

    function hideSuccess() {
        successMessage.classList.add('d-none');
    }
});
