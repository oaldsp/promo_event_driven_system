import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import axios from 'axios';
import { Bell, Flame, MinusCircle, PlusCircle, RefreshCw, Send, ThumbsDown, ThumbsUp, X } from 'lucide-react';
import './styles.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const api = axios.create({ baseURL: API_URL });

function App() {
  const [userId, setUserId] = useState(() => localStorage.getItem('promo_user_id') || 'consumidor-1');
  const [promotions, setPromotions] = useState([]);
  const [interests, setInterests] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [category, setCategory] = useState('eletronicos');
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    title: 'Headset sem fio',
    description: 'Cancelamento de ruido e bateria de longa duracao',
    category: 'eletronicos',
    price: '199.90',
    store_email: 'loja@example.com',
  });

  const hotDeals = useMemo(() => promotions.filter((promotion) => promotion.hot_deal), [promotions]);

  async function refresh() {
    const [promotionsResponse, interestsResponse] = await Promise.all([
      api.get('/promocoes'),
      api.get(`/usuarios/${encodeURIComponent(userId)}/interesses`),
    ]);
    setPromotions(promotionsResponse.data);
    setInterests(interestsResponse.data.categories);
  }

  useEffect(() => {
    localStorage.setItem('promo_user_id', userId);
    refresh().catch(console.error);

    const source = new EventSource(`${API_URL}/sse/${encodeURIComponent(userId)}`);
    source.addEventListener('notificacao', (event) => {
      const payload = JSON.parse(event.data);
      setNotifications((current) => [payload, ...current].slice(0, 20));
      refresh().catch(console.error);
    });

    return () => source.close();
  }, [userId]);

  async function submitPromotion(event) {
    event.preventDefault();
    setLoading(true);
    try {
      await api.post('/promocoes', { ...form, price: Number(form.price) });
      setForm((current) => ({ ...current, title: '', description: '', price: '' }));
      setTimeout(() => refresh().catch(console.error), 800);
    } finally {
      setLoading(false);
    }
  }

  async function vote(promotion, voteValue) {
    await api.post(`/promocoes/${promotion.id}/votos`, { user_id: userId, vote: voteValue });
  }

  async function addInterest(event) {
    event.preventDefault();
    await api.post(`/usuarios/${encodeURIComponent(userId)}/interesses`, { category });
    await refresh();
  }

  async function removeInterest(interest) {
    await api.delete(`/usuarios/${encodeURIComponent(userId)}/interesses/${encodeURIComponent(interest)}`);
    await refresh();
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <h1>Promo Deals</h1>
          <p>Promocoes publicadas, votos e notificacoes em tempo real por categoria.</p>
        </div>
        <label className="user-field">
          Usuario
          <input value={userId} onChange={(event) => setUserId(event.target.value)} />
        </label>
      </section>

      <section className="workspace">
        <aside className="panel side-panel">
          <h2>Cadastrar promocao</h2>
          <form onSubmit={submitPromotion} className="stack">
            <input placeholder="Titulo" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
            <textarea placeholder="Descricao" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
            <input placeholder="Categoria" value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} />
            <input placeholder="Preco" type="number" step="0.01" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} />
            <input placeholder="E-mail da loja" value={form.store_email} onChange={(event) => setForm({ ...form, store_email: event.target.value })} />
            <button className="primary" disabled={loading}>
              <Send size={18} />
              Enviar
            </button>
          </form>

          <h2>Interesses</h2>
          <form onSubmit={addInterest} className="inline-form">
            <input value={category} onChange={(event) => setCategory(event.target.value)} />
            <button title="Seguir categoria" aria-label="Seguir categoria">
              <PlusCircle size={20} />
            </button>
          </form>
          <div className="chips">
            {interests.map((interest) => (
              <span className="chip" key={interest}>
                {interest}
                <button onClick={() => removeInterest(interest)} title="Cancelar interesse" aria-label={`Cancelar interesse em ${interest}`}>
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        </aside>

        <section className="content">
          <div className="section-header">
            <div>
              <h2>Promocoes</h2>
              <span>{promotions.length} publicadas</span>
            </div>
            <button className="ghost" onClick={refresh} title="Atualizar" aria-label="Atualizar">
              <RefreshCw size={18} />
            </button>
          </div>

          <div className="promotion-grid">
            {promotions.map((promotion) => (
              <article className="promotion-card" key={promotion.id}>
                <header>
                  <span className="category">{promotion.category}</span>
                  {promotion.hot_deal && <span className="hot"><Flame size={15} /> Hot deal</span>}
                </header>
                <h3>{promotion.title}</h3>
                <p>{promotion.description}</p>
                <strong>R$ {Number(promotion.price).toFixed(2)}</strong>
                <footer>
                  <button onClick={() => vote(promotion, 'positivo')} title="Voto positivo" aria-label="Voto positivo">
                    <ThumbsUp size={18} />
                  </button>
                  <button onClick={() => vote(promotion, 'negativo')} title="Voto negativo" aria-label="Voto negativo">
                    <ThumbsDown size={18} />
                  </button>
                </footer>
              </article>
            ))}
            {!promotions.length && <p className="empty">Nenhuma promocao publicada ainda.</p>}
          </div>
        </section>

        <aside className="panel notifications">
          <h2><Bell size={18} /> Notificacoes SSE</h2>
          {hotDeals.length > 0 && (
            <div className="hot-list">
              {hotDeals.map((promotion) => (
                <span key={promotion.id}><Flame size={14} /> {promotion.title}</span>
              ))}
            </div>
          )}
          <div className="notification-list">
            {notifications.map((notification) => (
              <article key={notification.id} className="notification">
                <span>{notification.kind === 'hotdeal' ? 'Destaque' : notification.category}</span>
                <p>{notification.message}</p>
              </article>
            ))}
            {!notifications.length && <p className="empty">Aguardando eventos em tempo real.</p>}
          </div>
        </aside>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
