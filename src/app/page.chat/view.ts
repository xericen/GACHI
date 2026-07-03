import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    public draft: string = '';
    public isSending: boolean = false;
    public activeChatThreadId: string = '';
    public messages: any[] = [
        {
            role: 'assistant',
            text: '원하는 여행 분위기나 일정만 말해주시면 AI가 바로 코스로 정리해드릴게요.',
            seed: true
        }
    ];

    public suggestions: string[] = [
        '이번 주말 서울 데이트',
        '혼자 가기 좋은 바다',
        '부모님과 당일치기',
        '비 오는 날 실내 코스'
    ];

    public tabs: any[] = [
        { key: 'home', label: '홈', icon: 'fa-house' },
        { key: 'chat', label: '채팅', icon: 'fa-comments' },
        { key: 'map', label: '지도', icon: 'fa-map-location-dot' },
        { key: 'saved', label: '저장', icon: 'fa-bookmark' },
        { key: 'my', label: '마이', icon: 'fa-user' }
    ];

    constructor(public service: Service) { }

    public async ngOnInit() {
        await this.service.init();
        let prompt = this.consumeIncomingPrompt();
        if (prompt) {
            this.draft = prompt;
            await this.send();
            return;
        }
        await this.service.render();
    }

    public async selectSuggestion(value: string) {
        if (this.isSending) return;
        this.draft = value;
        await this.send();
    }

    public canSend() {
        return !this.isSending && String(this.draft || '').trim().length > 0;
    }

    public async send() {
        if (this.isSending) return;

        let prompt = String(this.draft || '').trim();
        if (!prompt) return;

        this.draft = '';
        this.messages.push({ role: 'user', text: prompt });

        let reply = {
            role: 'assistant',
            text: '답변을 준비하고 있어요...',
            loading: true
        };
        this.messages.push(reply);
        this.isSending = true;

        await this.service.render();
        this.scrollToLatest();

        try {
            let history = this.messages
                .filter((message: any) => !message.loading && !message.seed)
                .slice(0, -1)
                .slice(-12)
                .map((message: any) => ({
                    role: message.role,
                    text: String(message.text || '')
                }));

            let result: any = await wiz.call('send', {
                prompt: prompt,
                history: JSON.stringify(history),
                thread_id: this.activeChatThreadId
            });

            if (result && result.code === 200) {
                reply.text = result.reply || (result.data && result.data.reply) || '추천 결과를 가져오지 못했어요. 다시 질문해 주세요.';
                this.activeChatThreadId = result.thread_id || (result.data && result.data.thread_id) || this.activeChatThreadId;
            } else {
                reply.text = this.responseMessage(result, 'AI 연결에 실패했어요. 잠시 후 다시 시도해 주세요.');
            }
        } catch (e) {
            reply.text = 'AI 연결 중 오류가 발생했어요. 잠시 후 다시 시도해 주세요.';
        }

        reply.loading = false;
        this.isSending = false;
        await this.service.render();
        this.scrollToLatest();
    }

    public async handleEnter(event: any) {
        if (event.shiftKey) return;
        event.preventDefault();
        await this.send();
    }

    public formatMessage(value: any) {
        let escaped = String(value || '').replace(/[&<>"']/g, (char: string) => {
            let map: any = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return map[char] || char;
        });
        return escaped
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }

    public selectTab(tab: any) {
        if (tab.key === 'home') {
            this.service.href('/access?tab=home');
            return;
        }
        if (tab.key === 'chat') return;
        this.service.href(`/access?tab=${encodeURIComponent(tab.key)}`);
    }

    private responseMessage(result: any, fallback: string) {
        if (!result) return fallback;
        if (typeof result.message === 'string' && result.message) return result.message;
        if (typeof result.data === 'string' && result.data) return result.data;
        if (result.data && typeof result.data.message === 'string' && result.data.message) return result.data.message;
        return fallback;
    }

    private consumeIncomingPrompt() {
        let prompt = '';
        if (typeof window !== 'undefined') {
            let params = new URLSearchParams(window.location.search || '');
            prompt = params.get('prompt') || '';
            if (!prompt && window.sessionStorage) {
                try {
                    prompt = window.sessionStorage.getItem('tour-on-chat-prompt') || '';
                    window.sessionStorage.removeItem('tour-on-chat-prompt');
                } catch (e) { }
            }
        }
        return prompt.trim();
    }

    private scrollToLatest() {
        if (typeof window === 'undefined') return;
        window.setTimeout(() => {
            let list = document.querySelector('.message-list');
            if (list) list.scrollTop = list.scrollHeight;
        }, 0);
    }
}
