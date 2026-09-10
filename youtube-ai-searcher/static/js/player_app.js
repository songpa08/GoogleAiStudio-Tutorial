// AI YouTube Searcher - Player & Interactive Transcript Application

let ytPlayer = null;
let currentVideoData = null;
let currentTranscriptData = null;
let currentSegments = [];
let timeUpdateInterval = null;

// =========================================================================
// [1] 초기화 및 YouTube IFrame API 설정
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    initApiKeyManagement();
    initSearchForm();
    initPlayerControls();
    initTabs();
    initTranscriptFilter();
    initChat();
});

// YouTube IFrame API 준비 완료 콜백
function onYouTubeIframeAPIReady() {
    console.log("[YouTube API] IFrame API Ready");
}

function initYouTubePlayer(videoId) {
    const placeholder = document.getElementById("playerPlaceholder");
    const playerContainer = document.getElementById("youtubePlayer");

    placeholder.classList.add("hidden");
    playerContainer.classList.remove("hidden");

    if (ytPlayer && typeof ytPlayer.destroy === "function") {
        ytPlayer.destroy();
    }

    ytPlayer = new YT.Player("youtubePlayer", {
        height: "100%",
        width: "100%",
        videoId: videoId,
        playerVars: {
            autoplay: 1,
            playsinline: 1,
            rel: 0,
            modestbranding: 1,
            enablejsapi: 1,
        },
        events: {
            onReady: onPlayerReady,
            onStateChange: onPlayerStateChange,
        },
    });
}

function onPlayerReady(event) {
    console.log("[YouTube API] Player Ready");
    // 초기 볼륨 설정
    const volumeSlider = document.getElementById("volumeSlider");
    const initialVol = parseInt(volumeSlider.value) || 100;
    event.target.setVolume(initialVol);
    event.target.playVideo();

    // 재생 시간 업데이트 타이머 시작
    if (timeUpdateInterval) clearInterval(timeUpdateInterval);
    timeUpdateInterval = setInterval(updatePlayerProgress, 500);
}

function onPlayerStateChange(event) {
    const playBtn = document.getElementById("ctrlPlayBtn");
    if (!playBtn) return;

    if (event.data === YT.PlayerState.PLAYING) {
        playBtn.innerHTML = '<i data-lucide="pause" class="w-4 h-4"></i>';
        lucide.createIcons();
    } else {
        playBtn.innerHTML = '<i data-lucide="play" class="w-4 h-4"></i>';
        lucide.createIcons();
    }
}

// =========================================================================
// [2] 플레이어 커스텀 컨트롤러 (재생/일시정지, 볼륨, 10초 점프)
// =========================================================================
function initPlayerControls() {
    const playBtn = document.getElementById("ctrlPlayBtn");
    const bwdBtn = document.getElementById("ctrlBackwardBtn");
    const fwdBtn = document.getElementById("ctrlForwardBtn");
    const muteBtn = document.getElementById("ctrlMuteBtn");
    const volumeSlider = document.getElementById("volumeSlider");
    const volumeLabel = document.getElementById("volumeLabel");
    const volumeIcon = document.getElementById("volumeIcon");

    // 재생 / 일시정지 토글
    playBtn.addEventListener("click", () => {
        if (!ytPlayer || typeof ytPlayer.getPlayerState !== "function") return;
        const state = ytPlayer.getPlayerState();
        if (state === YT.PlayerState.PLAYING) {
            ytPlayer.pauseVideo();
        } else {
            ytPlayer.playVideo();
        }
    });

    // 10초 뒤로
    bwdBtn.addEventListener("click", () => {
        if (!ytPlayer || typeof ytPlayer.getCurrentTime !== "function") return;
        const cur = ytPlayer.getCurrentTime();
        seekToSeconds(Math.max(0, cur - 10));
    });

    // 10초 앞으로
    fwdBtn.addEventListener("click", () => {
        if (!ytPlayer || typeof ytPlayer.getCurrentTime !== "function") return;
        const cur = ytPlayer.getCurrentTime();
        seekToSeconds(cur + 10);
    });

    // 볼륨 슬라이더
    volumeSlider.addEventListener("input", (e) => {
        const val = parseInt(e.target.value);
        volumeLabel.textContent = `${val}%`;
        if (ytPlayer && typeof ytPlayer.setVolume === "function") {
            ytPlayer.setVolume(val);
            if (val === 0) {
                ytPlayer.mute();
            } else if (ytPlayer.isMuted()) {
                ytPlayer.unMute();
            }
        }
        updateVolumeIcon(val);
    });

    // 음소거 토글
    muteBtn.addEventListener("click", () => {
        if (!ytPlayer || typeof ytPlayer.isMuted !== "function") return;
        if (ytPlayer.isMuted()) {
            ytPlayer.unMute();
            const vol = ytPlayer.getVolume() || 100;
            volumeSlider.value = vol;
            volumeLabel.textContent = `${vol}%`;
            updateVolumeIcon(vol);
        } else {
            ytPlayer.mute();
            volumeSlider.value = 0;
            volumeLabel.textContent = "0%";
            updateVolumeIcon(0);
        }
    });
}

function updateVolumeIcon(vol) {
    const iconContainer = document.getElementById("ctrlMuteBtn");
    if (vol === 0) {
        iconContainer.innerHTML = '<i data-lucide="volume-x" class="w-4 h-4"></i>';
    } else if (vol < 50) {
        iconContainer.innerHTML = '<i data-lucide="volume-1" class="w-4 h-4"></i>';
    } else {
        iconContainer.innerHTML = '<i data-lucide="volume-2" class="w-4 h-4"></i>';
    }
    lucide.createIcons();
}

function seekToSeconds(sec) {
    if (!ytPlayer || typeof ytPlayer.seekTo !== "function") return;
    ytPlayer.seekTo(sec, true);
    ytPlayer.playVideo();
}

function formatSeconds(sec) {
    if (!sec || isNaN(sec)) return "00:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function updatePlayerProgress() {
    if (!ytPlayer || typeof ytPlayer.getCurrentTime !== "function") return;
    try {
        const cur = ytPlayer.getCurrentTime();
        const dur = ytPlayer.getDuration();

        document.getElementById("currentTimeLabel").textContent = formatSeconds(cur);
        if (dur) {
            document.getElementById("totalDurationLabel").textContent = formatSeconds(dur);
        }

        // 현재 시간에 따른 자막 하이라이트
        highlightCurrentTranscriptSegment(cur);
    } catch (e) {
        // player not ready
    }
}

// =========================================================================
// [3] 검색 및 비디오 처리 (Gemini 3.5 Transcribe STT)
// =========================================================================
function initSearchForm() {
    const form = document.getElementById("searchForm");
    const input = document.getElementById("youtubeUrlInput");
    const clearBtn = document.getElementById("clearInputBtn");

    input.addEventListener("input", () => {
        clearBtn.classList.toggle("hidden", !input.value);
    });

    clearBtn.addEventListener("click", () => {
        input.value = "";
        clearBtn.classList.add("hidden");
        input.focus();
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const url = input.value.trim();
        if (!url) return;

        await processVideoUrl(url);
    });
}

async function processVideoUrl(url) {
    const overlay = document.getElementById("loadingOverlay");
    const statusMsg = document.getElementById("loadingStatusMsg");
    const searchBtn = document.getElementById("searchBtn");

    const apiKey = getStoredApiKey();

    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
    searchBtn.disabled = true;
    statusMsg.textContent = "1단계: 오디오 추출 및 다운로드 중...";

    try {
        statusMsg.textContent = "2단계: Gemini AI 모델로 정밀 자막 및 타임스탬프 추출 중...";

        const response = await fetch("/api/process", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                url: url,
                api_key: apiKey,
                stt_model: "gemini-3.7-flash",
            }),
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.detail || "영상 처리에 실패했습니다.");
        }

        currentVideoData = data.video;
        currentTranscriptData = data.transcription;
        currentSegments = data.transcription.segments || [];

        // 1. YouTube IFrame 플레이어 실행
        initYouTubePlayer(currentVideoData.video_id);

        // 2. 비디오 메타데이터 렌더링
        renderVideoMetadata(currentVideoData, currentTranscriptData, data.from_cache, data.created_at);

        // 3. 자막 세그먼트 렌더링
        renderTranscriptList(currentSegments);

        // 4. Q&A 안내 초기화
        resetChatSession(currentVideoData.title);

    } catch (err) {
        alert("오류 발생: " + err.message);
    } finally {
        overlay.classList.remove("flex");
        overlay.classList.add("hidden");
        searchBtn.disabled = false;
    }
}

function renderVideoMetadata(video, transcription, fromCache = false, createdAt = "") {
    const card = document.getElementById("videoInfoCard");
    card.classList.remove("hidden");
    card.classList.add("flex");

    document.getElementById("videoTitle").textContent = video.title;
    document.getElementById("videoChannel").textContent = video.uploader || "YouTube Channel";
    document.getElementById("videoUploader").textContent = video.uploader;
    document.getElementById("videoDurationBadge").textContent = video.duration_formatted;
    document.getElementById("videoSizeBadge").textContent = `${video.file_size_mb} MB`;

    // CSV 캐시 상태 뱃지
    const cacheBadge = document.getElementById("cacheStatusBadge");
    const cacheText = document.getElementById("cacheStatusText");
    if (fromCache) {
        cacheBadge.classList.remove("hidden");
        cacheBadge.classList.add("inline-flex");
        cacheText.textContent = createdAt ? `CSV 저장본 (${createdAt})` : "CSV 저장본 로드";
    } else {
        cacheBadge.classList.remove("hidden");
        cacheBadge.classList.add("inline-flex");
        cacheBadge.className = "text-[11px] bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2.5 py-1 rounded-md font-medium inline-flex items-center gap-1";
        cacheText.textContent = "신규 전사 및 CSV 저장 완료";
    }
    lucide.createIcons();

    // 요약 표시
    const summaryBox = document.getElementById("summaryContent");
    if (transcription.summary) {
        summaryBox.innerHTML = marked.parse(transcription.summary);
    } else {
        summaryBox.textContent = "요약 정보가 제공되지 않았습니다.";
    }
}

// =========================================================================
// [4] 인터랙티브 자막 목록 & 실시간 검색 필터
// =========================================================================
function renderTranscriptList(segments) {
    const list = document.getElementById("transcriptList");
    const badge = document.getElementById("transcriptCountBadge");
    list.innerHTML = "";

    let effectiveSegments = segments || [];

    // 만약 세그먼트가 비어있다면, 전체 텍스트에서 클라이언트 사이드 파싱 재시도
    if (effectiveSegments.length === 0 && currentTranscriptData && currentTranscriptData.full_content) {
        effectiveSegments = extractSegmentsFromRawText(currentTranscriptData.full_content);
        currentSegments = effectiveSegments;
    }

    if (!effectiveSegments || effectiveSegments.length === 0) {
        list.innerHTML = `
            <div class="h-full flex flex-col items-center justify-center text-center p-6 text-yt-subtext">
                <i data-lucide="info" class="w-8 h-8 mb-2 opacity-50"></i>
                <p class="text-xs">타임스탬프 세그먼트가 없습니다.<br/>우측 상단 API Key를 확인하거나 다시 시도해주세요.</p>
            </div>
        `;
        lucide.createIcons();
        badge.classList.add("hidden");
        return;
    }

    badge.textContent = `${effectiveSegments.length}개 구간`;
    badge.classList.remove("hidden");

    effectiveSegments.forEach((seg, idx) => {
        const item = document.createElement("div");
        item.id = `seg-item-${idx}`;
        item.className = "transcript-item p-2.5 rounded-xl bg-[#181818] border border-yt-border/60 hover:border-yt-border flex items-start gap-3 cursor-pointer group";
        item.dataset.seconds = seg.seconds;
        item.dataset.index = idx;

        item.innerHTML = `
            <button class="ts-clickable flex-shrink-0 bg-blue-600/20 group-hover:bg-yt-red text-blue-400 group-hover:text-white px-2 py-1 rounded-md text-[11px] font-mono font-bold transition" title="이 시간으로 이동">
                ${seg.timestamp}
            </button>
            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-0.5">
                    <span class="text-[11px] font-semibold text-white/90">${seg.speaker}</span>
                </div>
                <p class="text-xs text-slate-300 leading-relaxed break-words">${seg.text}</p>
            </div>
        `;

        // 클릭 시 영상 점프
        item.addEventListener("click", () => {
            seekToSeconds(seg.seconds);
        });

        list.appendChild(item);
    });

    lucide.createIcons();
}

function initTranscriptFilter() {
    const input = document.getElementById("filterInput");
    const clearBtn = document.getElementById("clearFilterBtn");

    input.addEventListener("input", () => {
        const query = input.value.trim().toLowerCase();
        clearBtn.classList.toggle("hidden", !query);

        if (!currentSegments) return;

        const filtered = currentSegments.filter(seg => 
            seg.text.toLowerCase().includes(query) ||
            seg.speaker.toLowerCase().includes(query) ||
            seg.timestamp.includes(query)
        );

        renderTranscriptList(filtered);
    });

    clearBtn.addEventListener("click", () => {
        input.value = "";
        clearBtn.classList.add("hidden");
        renderTranscriptList(currentSegments);
        input.focus();
    });

    // 전체 자막 복사
    document.getElementById("copyAllTranscriptBtn").addEventListener("click", () => {
        if (!currentTranscriptData) {
            alert("복사할 자막이 없습니다.");
            return;
        }
        navigator.clipboard.writeText(currentTranscriptData.full_content || "").then(() => {
            alert("전체 자막 및 요약이 클립보드에 복사되었습니다!");
        });
    });
}

function highlightCurrentTranscriptSegment(currentSec) {
    if (!currentSegments || currentSegments.length === 0) return;

    let activeIdx = -1;
    for (let i = 0; i < currentSegments.length; i++) {
        if (currentSec >= currentSegments[i].seconds) {
            activeIdx = i;
        } else {
            break;
        }
    }

    document.querySelectorAll(".transcript-item").forEach((el, idx) => {
        if (idx === activeIdx) {
            el.classList.add("active-playing");
        } else {
            el.classList.remove("active-playing");
        }
    });
}

// =========================================================================
// [5] 탭 전환 (자막 탭 vs AI Q&A 탭)
// =========================================================================
function initTabs() {
    const tabTrans = document.getElementById("tabTranscriptBtn");
    const tabChat = document.getElementById("tabChatBtn");
    const panelTrans = document.getElementById("transcriptPanel");
    const panelChat = document.getElementById("chatPanel");

    tabTrans.addEventListener("click", () => {
        tabTrans.classList.add("text-white", "border-yt-red");
        tabTrans.classList.remove("text-yt-subtext", "border-transparent");
        tabChat.classList.remove("text-white", "border-yt-red");
        tabChat.classList.add("text-yt-subtext", "border-transparent");

        panelTrans.classList.remove("hidden");
        panelChat.classList.add("hidden");
    });

    tabChat.addEventListener("click", () => {
        tabChat.classList.add("text-white", "border-yt-red");
        tabChat.classList.remove("text-yt-subtext", "border-transparent");
        tabTrans.classList.remove("text-white", "border-yt-red");
        tabTrans.classList.add("text-yt-subtext", "border-transparent");

        panelChat.classList.remove("hidden");
        panelTrans.classList.add("hidden");
    });
}

// =========================================================================
// [6] Gemini 3.8 Flash AI Q&A 채팅
// =========================================================================
function initChat() {
    const form = document.getElementById("chatForm");
    const input = document.getElementById("chatInput");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = input.value.trim();
        if (!question) return;

        if (!currentTranscriptData) {
            alert("먼저 상단에서 YouTube 영상을 검색하여 자막을 추출해주세요.");
            return;
        }

        appendChatMessage("user", question);
        input.value = "";

        const loadingId = appendLoadingMessage();

        try {
            const apiKey = getStoredApiKey();
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    video_title: currentVideoData ? currentVideoData.title : "영상",
                    transcript_text: currentTranscriptData.full_content,
                    api_key: apiKey,
                    qa_model: "gemini-3.8-flash",
                }),
            });

            const data = await response.json();
            removeLoadingMessage(loadingId);

            if (!response.ok || !data.success) {
                throw new Error(data.detail || "답변 생성 실패");
            }

            appendChatMessage("ai", data.data.answer);

        } catch (err) {
            removeLoadingMessage(loadingId);
            appendChatMessage("ai", `❌ 오류: ${err.message}`);
        }
    });
}

function resetChatSession(videoTitle) {
    const container = document.getElementById("chatMessages");
    container.innerHTML = `
        <div class="bg-[#181818] border border-yt-border rounded-xl p-3.5 text-xs text-slate-300 flex items-start gap-2.5">
            <div class="w-6 h-6 rounded-full bg-indigo-600/30 text-indigo-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                <i data-lucide="bot" class="w-3.5 h-3.5"></i>
            </div>
            <div class="flex-1 leading-relaxed">
                <p class="font-semibold text-white mb-1">Gemini 3.8 Flash 비디오 AI</p>
                <p>《${videoTitle}》 영상의 분석이 완료되었습니다. 궁금한 점이나 특정 내용의 위치를 물어보세요!</p>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function appendChatMessage(role, text) {
    const container = document.getElementById("chatMessages");
    const msgBox = document.createElement("div");

    if (role === "user") {
        msgBox.className = "flex justify-end";
        msgBox.innerHTML = `
            <div class="bg-yt-red/90 text-white rounded-2xl rounded-tr-sm px-3.5 py-2.5 text-xs max-w-[85%] leading-relaxed shadow">
                ${escapeHtml(text)}
            </div>
        `;
    } else {
        msgBox.className = "bg-[#181818] border border-yt-border rounded-xl p-3.5 text-xs text-slate-300 flex items-start gap-2.5";
        
        // 타임스탬프 링크 변환 ([00:15] -> 클릭 가능한 배지)
        const parsedHtml = formatChatTimestamps(marked.parse(text));

        msgBox.innerHTML = `
            <div class="w-6 h-6 rounded-full bg-indigo-600/30 text-indigo-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
            </div>
            <div class="flex-1 leading-relaxed prose prose-invert max-w-none">
                ${parsedHtml}
            </div>
        `;
    }

    container.appendChild(msgBox);
    container.scrollTop = container.scrollHeight;
    lucide.createIcons();
}

function formatChatTimestamps(html) {
    // [MM:SS] 또는 [HH:MM:SS] 매칭
    return html.replace(/\[(\d{1,2}:\d{2}(?::\d{2})?)\]/g, (match, p1) => {
        const sec = parseTimestampToSeconds(p1);
        return `<button onclick="seekToSeconds(${sec})" class="ts-clickable inline-flex items-center gap-1 bg-blue-600/30 hover:bg-yt-red text-blue-300 hover:text-white px-1.5 py-0.5 rounded font-mono font-bold text-[11px] transition" title="${p1} 위치로 이동">▶ ${match}</button>`;
    });
}

function parseTimestampToSeconds(tsStr) {
    const parts = tsStr.split(":").map(Number);
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    return 0;
}

function appendLoadingMessage() {
    const container = document.getElementById("chatMessages");
    const id = "loading-" + Date.now();
    const box = document.createElement("div");
    box.id = id;
    box.className = "bg-[#181818] border border-yt-border rounded-xl p-3.5 text-xs text-yt-subtext flex items-center gap-2";
    box.innerHTML = `
        <div class="w-3.5 h-3.5 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
        <span>Gemini 3.8 Flash가 영상 내용을 분석 중입니다...</span>
    `;
    container.appendChild(box);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function escapeHtml(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// =========================================================================
// [7] API Key 모달 관리
// =========================================================================
function initApiKeyManagement() {
    const modal = document.getElementById("apiKeyModal");
    const openBtn = document.getElementById("apiKeyModalBtn");
    const closeBtn = document.getElementById("closeApiKeyModalBtn");
    const cancelBtn = document.getElementById("cancelApiKeyBtn");
    const saveBtn = document.getElementById("saveApiKeyBtn");
    const input = document.getElementById("modalApiKeyInput");
    const statusText = document.getElementById("apiKeyStatusText");

    const updateStatus = () => {
        const key = getStoredApiKey();
        if (key) {
            statusText.textContent = "API Key 설정됨";
            statusText.classList.add("text-emerald-400");
        } else {
            statusText.textContent = "API Key 설정";
            statusText.classList.remove("text-emerald-400");
        }
    };

    updateStatus();

    openBtn.addEventListener("click", () => {
        input.value = getStoredApiKey() || "";
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        input.focus();
    });

    const closeModal = () => {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    };

    closeBtn.addEventListener("click", closeModal);
    cancelBtn.addEventListener("click", closeModal);

    saveBtn.addEventListener("click", () => {
        const key = input.value.trim();
        if (key) {
            localStorage.setItem("GEMINI_API_KEY", key);
        } else {
            localStorage.removeItem("GEMINI_API_KEY");
        }
        updateStatus();
        closeModal();
    });
}

function getStoredApiKey() {
    return localStorage.getItem("GEMINI_API_KEY") || "";
}

function extractSegmentsFromRawText(rawText) {
    if (!rawText) return [];
    const segments = [];
    const lines = rawText.split("\n");

    for (let line of lines) {
        line = line.trim();
        if (!line) continue;

        const match = line.match(/\[?(\b\d{1,2}:\d{2}(?::\d{2})?\b)\]?/);
        if (match) {
            const rawTs = match[1];
            const seconds = parseTimestampToSeconds(rawTs);
            let content = line.substring(line.indexOf(match[0]) + match[0].length).trim();
            content = content.replace(/^[:*\-\]]+/, "").trim();

            let speaker = "화자";
            let text = content;
            const spMatch = content.match(/^\*{0,2}([^:*_]{1,20})\*{0,2}[:：]\s*(.*)$/);
            if (spMatch) {
                speaker = spMatch[1].replace(/[*_]/g, "").trim();
                text = spMatch[2].trim();
            }

            if (text) {
                segments.push({
                    timestamp: rawTs.includes(":") ? rawTs : `00:${rawTs}`,
                    seconds: seconds,
                    speaker: speaker,
                    text: text,
                    raw_line: line,
                });
            }
        }
    }
    return segments;
}
