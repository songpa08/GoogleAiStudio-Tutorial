// Global state
let currentData = {
    video: null,
    transcription: null,
    activeTab: 'summary'
};

let timerInterval = null;
let startTime = 0;

document.addEventListener('DOMContentLoaded', () => {
    const youtubeUrlInput = document.getElementById('youtubeUrl');
    const transcribeBtn = document.getElementById('transcribeBtn');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const copyBtn = document.getElementById('copyBtn');

    // Enter key trigger
    youtubeUrlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            startTranscription();
        }
    });

    // Transcribe button click
    transcribeBtn.addEventListener('click', startTranscription);

    // Tab switching
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    // Copy to clipboard
    copyBtn.addEventListener('click', copyActiveTabContent);
});

function switchTab(tabName) {
    currentData.activeTab = tabName;

    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        const isCurrent = btn.getAttribute('data-tab') === tabName;
        if (isCurrent) {
            btn.className = 'tab-btn px-4 py-2.5 text-xs font-semibold rounded-t-lg border-b-2 border-indigo-500 text-indigo-400 flex items-center gap-1.5 transition-all';
        } else {
            btn.className = 'tab-btn px-4 py-2.5 text-xs font-semibold rounded-t-lg border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-all';
        }
    });

    // Update panel visibility
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });

    const activePanel = document.getElementById(`tabContent-${tabName}`);
    if (activePanel) {
        activePanel.classList.remove('hidden');
    }
}

async function startTranscription() {
    const urlInput = document.getElementById('youtubeUrl');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const modelSelect = document.getElementById('modelSelect');

    const url = urlInput.value.trim();
    const apiKey = apiKeyInput.value.trim();
    const model = modelSelect.value;

    if (!url) {
        showError('유튜브 영상 링크(URL)를 입력해주세요.');
        return;
    }

    hideError();
    showProgress();
    setStep(1, '영상 정보 확인 중...');

    try {
        // Step 2: Download & Transcribe
        setStep(2, '오디오 스트림 다운로드 중...');

        const response = await fetch('/api/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                api_key: apiKey || null,
                model: model
            }),
        });

        setStep(3, 'Gemini AI 음성 인식 및 트랜스크립트 분석 중...');

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.detail || '전사 처리 중 오류가 발생했습니다.');
        }

        // Render result
        renderResults(result);
        hideProgress();

    } catch (err) {
        hideProgress();
        showError(err.message || '서버와의 통신에 실패했습니다.');
    }
}

function renderResults(data) {
    currentData.video = data.video;
    currentData.transcription = data.transcription;

    // Set video details
    document.getElementById('videoThumb').src = data.video.thumbnail || '';
    document.getElementById('videoTitle').textContent = data.video.title || '제목 없음';
    document.getElementById('videoUploader').textContent = data.video.uploader || '알 수 없음';
    document.getElementById('videoDuration').textContent = `⏱️ ${data.video.duration_formatted || ''}`;
    document.getElementById('audioSize').textContent = `💾 ${data.video.file_size_mb || 0} MB`;
    document.getElementById('usedModelBadge').textContent = `AI: ${data.transcription.model_used}`;

    // Set Audio Player
    const audioPlayer = document.getElementById('audioPlayer');
    audioPlayer.src = data.video.audio_url;

    // Render contents
    const markedOptions = { breaks: true, gfm: true };

    const summaryHtml = marked.parse(data.transcription.summary || '요약 정보가 없습니다.', markedOptions);
    document.getElementById('tabContent-summary').innerHTML = summaryHtml;

    const timestampsHtml = marked.parse(data.transcription.timestamps || '타임스탬프 정보가 없습니다.', markedOptions);
    document.getElementById('tabContent-timestamps').innerHTML = timestampsHtml;

    const transcriptHtml = marked.parse(data.transcription.transcript || data.transcription.full_content || '전사 텍스트가 없습니다.', markedOptions);
    document.getElementById('tabContent-transcript').innerHTML = transcriptHtml;

    // Show result section
    document.getElementById('resultSection').classList.remove('hidden');
    switchTab('summary');

    // Re-initialize Lucide icons
    lucide.createIcons();
}

function showProgress() {
    document.getElementById('resultSection').classList.add('hidden');
    document.getElementById('progressSection').classList.remove('hidden');
    
    startTime = Date.now();
    const progressTime = document.getElementById('progressTime');
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const s = String(elapsed % 60).padStart(2, '0');
        progressTime.textContent = `${m}:${s}`;
    }, 1000);
}

function hideProgress() {
    document.getElementById('progressSection').classList.add('hidden');
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function setStep(stepNum, title) {
    document.getElementById('progressStepTitle').textContent = title;
    const bar = document.getElementById('progressBar');

    if (stepNum === 1) {
        bar.style.width = '25%';
    } else if (stepNum === 2) {
        bar.style.width = '60%';
    } else if (stepNum === 3) {
        bar.style.width = '85%';
    }
}

function showError(msg) {
    const errorBox = document.getElementById('errorBox');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = msg;
    errorBox.classList.remove('hidden');
}

function hideError() {
    document.getElementById('errorBox').classList.add('hidden');
}

function copyActiveTabContent() {
    if (!currentData.transcription) return;

    let textToCopy = '';
    if (currentData.activeTab === 'summary') {
        textToCopy = currentData.transcription.summary;
    } else if (currentData.activeTab === 'timestamps') {
        textToCopy = currentData.transcription.timestamps;
    } else {
        textToCopy = currentData.transcription.transcript || currentData.transcription.full_content;
    }

    navigator.clipboard.writeText(textToCopy).then(() => {
        const copyText = document.getElementById('copyText');
        copyText.textContent = '복사 완료!';
        setTimeout(() => {
            copyText.textContent = '복사하기';
        }, 2000);
    });
}

function downloadAsFile(format) {
    if (!currentData.transcription) return;

    const title = (currentData.video ? currentData.video.title : 'transcript').replace(/[/\\?%*:|"<>]/g, '_');
    let content = '';
    let mimeType = 'text/plain;charset=utf-8';
    let filename = `${title}.${format}`;

    if (format === 'txt') {
        content = `[영상 제목]: ${currentData.video.title}\n[채널]: ${currentData.video.uploader}\n\n=== 핵심 요약 ===\n${currentData.transcription.summary}\n\n=== 타임스탬프 및 대화 ===\n${currentData.transcription.timestamps}\n\n=== 전체 전문 ===\n${currentData.transcription.transcript}`;
    } else if (format === 'md') {
        content = `# ${currentData.video.title}\n\n- **채널**: ${currentData.video.uploader}\n- **길이**: ${currentData.video.duration_formatted}\n\n## 💡 핵심 요약\n${currentData.transcription.summary}\n\n## ⏱️ 타임스탬프 및 대화\n${currentData.transcription.timestamps}\n\n## 📝 전체 전문\n${currentData.transcription.transcript}`;
        mimeType = 'text/markdown;charset=utf-8';
    } else if (format === 'srt') {
        content = convertToSrt(currentData.transcription.timestamps || currentData.transcription.transcript);
        mimeType = 'application/x-subrip;charset=utf-8';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function convertToSrt(rawText) {
    // [MM:SS] 패턴을 찾아 SRT 포맷으로 변환
    const lines = rawText.split('\n');
    let srtOutput = [];
    let count = 1;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        const match = line.match(/\[(\d{1,2}):(\d{2})\]/);
        if (match) {
            const min = parseInt(match[1], 10);
            const sec = parseInt(match[2], 10);
            const startTimeStr = `00:${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')},000`;
            const endTimeStr = `00:${String(min).padStart(2, '0')}:${String(sec + 4).padStart(2, '0')},000`;
            const textContent = line.replace(/\[\d{1,2}:\d{2}\]/, '').replace(/^[*_\s-]+/, '').trim();

            srtOutput.push(`${count}`);
            srtOutput.push(`${startTimeStr} --> ${endTimeStr}`);
            srtOutput.push(`${textContent}`);
            srtOutput.push('');
            count++;
        }
    }

    if (srtOutput.length === 0) {
        return `1\n00:00:00,000 --> 00:01:00,000\n${rawText}\n`;
    }

    return srtOutput.join('\n');
}
