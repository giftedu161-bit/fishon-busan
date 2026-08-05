window.fishonAi = {
  async request(imageElement, endpoint) {
    const response = await fetch(imageElement.src);
    const blob = await response.blob();
    const form = new FormData();
    form.append('image', blob, 'catch.jpg');
    const api = window.FISHON_AI_API_URL.replace(/\/$/, '');
    const result = await fetch(`${api}/${endpoint}`, { method: 'POST', body: form });
    if (!result.ok) throw new Error(`AI 서버 오류 (${result.status})`);
    return result.json();
  },
  async analyze(imageElement) { return this.request(imageElement, 'analyze'); },
  async analyzeGemini(imageElement) { return this.request(imageElement, 'analyze-gemini'); }
};
