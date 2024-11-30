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

            // Get the processed file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // Create and trigger download
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'processed_audio.mp3';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // Show success message
            showSuccess('Processing complete! Your file has been downloaded.');
            
        } catch (error) {
            showError(error.message);
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
