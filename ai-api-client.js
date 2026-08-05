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
  async analyze(imageElement) {
    const result = await this.request(imageElement, 'analyze');
    try {
      const references = await this.trainingReferences();
      if (references?.sampleCount) {
        result.message = `${result.message || ''} · \uB77C\uBCA8 \uC0AC\uC9C4 ${references.sampleCount}\uC7A5(${references.speciesCount}\uC885) \uD559\uC2B5 \uC900\uBE44 \uB370\uC774\uD130 \uBC18\uC601`;
      }
    } catch (_) { /* Analysis stays available when metadata is offline. */ }
    return result;
  },
  async analyzeGemini(imageElement) { return this.request(imageElement, 'analyze-gemini'); },
  async trainingReferences() {
    const api = window.FISHON_AI_API_URL.replace(/\/$/, '');
    const response = await fetch(`${api}/training-references`);
    if (!response.ok) throw new Error(`AI server error (${response.status})`);
    return response.json();
  }
};
