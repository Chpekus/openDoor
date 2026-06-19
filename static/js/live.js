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
            document.getElementById('stream-frames').textContent = data.stream_frames;
            document.getElementById('processed-frames').textContent = data.processed_frames;

            const serverTime = new Date(data.server_time);
            document.getElementById('server-time').textContent = serverTime.toLocaleTimeString('ru-RU');
        })
        .catch(error => console.error('Error updating stats:', error));
}
