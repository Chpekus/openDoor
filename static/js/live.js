// JavaScript для страницы лайв-трансляции

document.addEventListener('DOMContentLoaded', function() {
    const streamFrame = document.getElementById('stream-frame');
    const loadingDiv = document.getElementById('loading');
    
    connectStream();
    
    // Обновляем статистику каждые 1 секунду
    setInterval(updateStats, 1000);
});

function connectStream() {
    const streamFrame = document.getElementById('stream-frame');
    const loadingDiv = document.getElementById('loading');
    // HTTP-страница опубликована через порт 5096, а TCP-проброс WebSocket
    // напрямую на Gunicorn доступен через внешний порт 4106.
    const socket = new WebSocket(`ws://${window.location.hostname}:4106/ws/stream`);
    socket.binaryType = 'blob';

    socket.onmessage = event => {
        const url = URL.createObjectURL(event.data);
        const previousUrl = streamFrame.dataset.objectUrl;
        streamFrame.onload = () => {
            if (previousUrl) URL.revokeObjectURL(previousUrl);
        };
        streamFrame.dataset.objectUrl = url;
        streamFrame.src = url;
        streamFrame.classList.remove('is-hidden');
        loadingDiv.classList.add('is-hidden');
    };

    socket.onerror = error => console.error('Stream WebSocket error:', error);
    socket.onclose = () => {
        loadingDiv.classList.remove('is-hidden');
        setTimeout(connectStream, 1000);
    };
}

function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('stream-fps').textContent = data.stream_fps;
            document.getElementById('processed-fps').textContent = data.processed_fps;

            const streamError = document.getElementById('stream-error');
            const streamFrame = document.getElementById('stream-frame');
            const showStreamError = data.stream_open_failures >= 3;
            streamError.classList.toggle('is-hidden', !showStreamError);
            if (showStreamError) {
                streamFrame.classList.add('is-hidden');
            }

            const serverTime = new Date(data.server_time);
            document.getElementById('server-time').textContent = serverTime.toLocaleTimeString('ru-RU');
        })
        .catch(error => console.error('Error updating stats:', error));
}
