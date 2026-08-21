import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendChatQuery = async (query, filterSources = null, minConfidence = null) => {
  const response = await api.post('/chat', {
    query,
    filter_sources: filterSources,
    min_confidence: minConfidence,
  });
  return response.data;
};

export const uploadNmapScan = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/scan', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const searchThreatIntel = async (query = '', source = null, limit = 50) => {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  if (source) params.append('source', source);
  params.append('limit', limit);
  const response = await api.get(`/api/v1/intel/search?${params.toString()}`);
  return response.data;
};

export const queryAEGIS = sendChatQuery;
export const getSystemDiagnostics = async () => {
  const response = await api.get('/api/v1/system');
  return response.data;
};
export const getKnowledgeBaseStats = getStats;
export const getIngestionStatus = async () => {
  const response = await api.get('/stats');
  return response.data;
};
export const triggerIngestion = async (sources = null, limit = 50) => {
  return { status: "queued" };
};
export const syncSource = async (source, limit = 50) => {
  return { status: "completed" };
};

export default api;
