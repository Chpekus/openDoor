// JavaScript для страницы лайв-трансляции

document.addEventListener('DOMContentLoaded', function() {
    const streamFrame = document.getElementById('stream-frame');
    const loadingDiv = document.getElementById('loading');
    
    // Обновляем кадр каждые 500ms
    setInterval(updateStream, 500);
    
    // Обновляем статистику каждые 1 секунду
    setInterval(updateStats, 1000);
});

function updateStream() {
    const streamFrame = document.getElementById('stream-frame');
    const loadingDiv = document.getElementById('loading');
    
    fetch('/api/current_frame')
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch frame');
            return response.json();
        })
        .then(data => {
            if (data.frame) {
                streamFrame.src = 'data:image/jpeg;base64,' + data.frame;
                streamFrame.classList.remove('is-hidden');
                loadingDiv.classList.add('is-hidden');
            }
        })
        .catch(error => {
            console.error('Error updating stream:', error);
            loadingDiv.innerHTML = '⚠️ Ошибка загрузки потока';
        });
}

function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('fps').textContent = data.fps.toFixed(2);
            document.getElementById('frame-count').textContent = data.frames_in_window;
            
            const now = new Date();
            document.getElementById('last-update').textContent = now.toLocaleTimeString('ru-RU');
        })
        .catch(error => console.error('Error updating stats:', error));
}
