document.addEventListener('DOMContentLoaded', function() {
    // Элементы
    const videoFileInput = document.getElementById('video-file');
    const videoUrlInput = document.getElementById('video-url');
    const videoUploadBtn = document.getElementById('upload-video-btn');
    const pasteUrlBtn = document.getElementById('paste-url-btn');
    const videoFileInfo = document.getElementById('video-file-info');
    
    const presentationFileInput = document.getElementById('presentation-file');
    const presentationUploadBtn = document.getElementById('upload-presentation-btn');
    const presentationFileInfo = document.getElementById('presentation-file-info');
    
    const processBtn = document.getElementById('process-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    const resultSection = document.getElementById('result-section');
    const downloadBtn = document.getElementById('download-btn');
    const tryAgainBtn = document.getElementById('try-again-btn');

    // Состояние
    let videoSource = null; // 'file' или 'url'
    let videoData = null;   // File объект или URL строка
    let presentationFile = null;

    // Инициализация
    initEventListeners();

    function initEventListeners() {
        videoUploadBtn.addEventListener('click', () => {
            videoFileInput.click();
            hideUrlInput();
        });
        
        pasteUrlBtn.addEventListener('click', showUrlInput);
        
        videoFileInput.addEventListener('change', handleVideoFileUpload);
        videoUrlInput.addEventListener('input', handleVideoUrlInput);
        
        presentationUploadBtn.addEventListener('click', () => presentationFileInput.click());
        presentationFileInput.addEventListener('change', handlePresentationUpload);
        
        processBtn.addEventListener('click', startProcessing);
        tryAgainBtn.addEventListener('click', resetForm);
    }

    function showUrlInput() {
        videoUrlInput.style.display = 'block';
        videoUrlInput.focus();
        pasteUrlBtn.style.display = 'none';
        videoUploadBtn.textContent = 'Загрузить видео';
        resetVideoFile();
    }

    function hideUrlInput() {
        videoUrlInput.style.display = 'none';
        videoUrlInput.value = '';
        pasteUrlBtn.style.display = 'inline-block';
    }

    function handleVideoFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        videoSource = 'file';
        videoData = file;
        videoFileInfo.textContent = `Видео: ${file.name} (${formatSize(file.size)})`;
        hideUrlInput();
        updateProcessButton();
    }

    function handleVideoUrlInput(e) {
        const url = e.target.value.trim();
        
        if (!url) {
            videoSource = null;
            videoData = null;
            videoFileInfo.textContent = '';
            updateProcessButton();
            return;
        }
        
        if (!isValidUrl(url)) {
            videoFileInfo.textContent = 'Введите корректный URL видео';
            videoFileInfo.style.color = 'red';
            videoSource = null;
            videoData = null;
            return;
        }
        
        videoSource = 'url';
        videoData = url;
        videoFileInfo.textContent = `Видео по ссылке: ${url}`;
        videoFileInfo.style.color = '';
        updateProcessButton();
    }

    function handlePresentationUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        presentationFile = file;
        presentationFileInfo.textContent = `Презентация: ${file.name} (${formatSize(file.size)})`;
        updateProcessButton();
    }

    function updateProcessButton() {
        processBtn.disabled = !(videoData !== null);
    }

    function startProcessing() {
        if (!videoData) return;
        
        progressContainer.style.display = 'block';
        processBtn.disabled = true;
        resultSection.style.display = 'none';
        progressBar.style.width = '0%';
        progressText.innerHTML = '<span class="spinner">⏳</span> Идёт обработка...';
        
        // Подготовка данных для отправки
        const formData = new FormData();
        
        if (videoSource === 'file') {
            formData.append('video_file', videoData);
        } else {
            formData.append('video_url', videoData);
        }
        
        if (presentationFile) {
            formData.append('presentation_file', presentationFile);
        }
        
        // Отправка данных на сервер
        fetch('/api/process', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сервера');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                updateProgress(100);
                setTimeout(() => finishProcessing(true, data.download_url), 500);
            } else {
                throw new Error(data.message || 'Ошибка обработки');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('error-text').textContent = error.message;
            finishProcessing(false);
        });
        
        // Прогресс бар (симуляция для демонстрации)
        simulateProgress();
    }

    function simulateProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            if (progress >= 90) {
                clearInterval(interval);
                return;
            }
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            updateProgress(progress);
        }, 500);
    }

    function updateProgress(progress) {
        progressBar.style.width = `${progress}%`;
        progressText.innerHTML = `<span class="spinner">⏳</span> Обработка: ${Math.round(progress)}%`;
    }

    function finishProcessing(success, downloadUrl = null) {
        progressContainer.style.display = 'none';
        resultSection.style.display = 'block';
        
        if (success) {
            document.getElementById('success-message').style.display = 'block';
            document.getElementById('error-message').style.display = 'none';
            if (downloadUrl) {
                downloadBtn.href = downloadUrl;
            }
        } else {
            document.getElementById('success-message').style.display = 'none';
            document.getElementById('error-message').style.display = 'block';
        }
    }

    function resetVideoFile() {
        videoFileInput.value = '';
        videoSource = null;
        videoData = null;
        videoFileInfo.textContent = '';
        updateProcessButton();
    }

    function resetForm() {
        resetVideoFile();
        videoUrlInput.value = '';
        hideUrlInput();
        
        presentationFileInput.value = '';
        presentationFile = null;
        presentationFileInfo.textContent = '';
        
        progressBar.style.width = '0%';
        resultSection.style.display = 'none';
        processBtn.disabled = true;
    }

    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    function formatSize(bytes) {
        if (!bytes) return '0B';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return parseFloat((bytes / Math.pow(1024, i)).toFixed(1)) + sizes[i];
    }
});