// dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadBox = document.querySelector('.upload-box');

    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.style.background = 'var(--bg-green)';
    });

    uploadBox.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadBox.style.background = 'var(--white)';
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.style.background = 'var(--white)';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file');
            return;
        }

        const formData = new FormData();
        formData.append('image', file);

        // Send the image to the server
        fetch('/detect', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            alert('Prediction Result: ' + data.result);
        })
        .catch(error => {
            console.error('Error uploading image:', error);
            alert('Error uploading image');
        });
    }
});
