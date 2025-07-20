// audio_capture.js

let mediaRecorder;
let audioChunks = [];

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                let blob = new Blob(audioChunks, { type: 'audio/wav' });
                let url = URL.createObjectURL(blob);
                document.getElementById('audio').src = url;

                // Save audio blob URL to hidden input
                document.getElementById('audio_blob').value = URL.createObjectURL(blob);
                document.getElementById('audio_data').value = URL.createObjectURL(blob);
            };

            mediaRecorder.start();
            console.log('Recording started...');
        })
        .catch(error => console.error('Error accessing audio:', error));
}

function stopRecording() {
    if (mediaRecorder) {
        mediaRecorder.stop();
        console.log('Recording stopped...');
    }
}
