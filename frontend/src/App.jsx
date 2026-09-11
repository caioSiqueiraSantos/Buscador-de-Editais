import { useEffect, useState, useMemo } from 'react'
import logo from './assets/NIT Logo.png';
import GerenciadorTemas from './components/GerenciadorTemas';

function App() {
  const [oportunidades, setOportunidades] = useState([])
  const [busca, setBusca] = useState("")
  const [filtroTema, setFiltroTema] = useState("")
  const [filtroPrazo, setFiltroPrazo] = useState("")
  const [loading, setLoading] = useState(true)
  const [temasBanco, setTemasBanco] = useState([])
  const [isModalTemasOpen, setIsModalTemasOpen] = useState(false)
  const [editalSelecionado, setEditalSelecionado] = useState(null)

  const carregarOportunidades = () => {
    fetch('http://localhost:8000/oportunidades')
      .then(response => response.json())
      .then(data => {
        setOportunidades(data)
        setLoading(false)
      })
      .catch(error => {
        console.error("Erro ao buscar dados:", error)
        setLoading(false)
      })
  }

  const carregarTemasBanco = () => {
    fetch('http://localhost:8000/temas')
      .then(response => response.json())
      .then(data => setTemasBanco(data))
      .catch(error => console.error("Erro ao buscar temas:", error))
  }

  useEffect(() => {
    carregarOportunidades()
    carregarTemasBanco()
  }, [])

  // Extração de valores únicos para os filtros
  const temasUnicos = useMemo(() => {
    const temasOps = oportunidades.map(op => op.tematica).filter(Boolean)
    const temasDb = temasBanco.map(t => t.nome).filter(Boolean)
    return [...new Set([...temasOps, ...temasDb])].sort()
  }, [oportunidades, temasBanco])

  const prazosUnicos = useMemo(() => {
    const prazos = oportunidades.map(op => op.prazo).filter(Boolean)
    return [...new Set(prazos)].sort()
  }, [oportunidades])

  const filtradas = oportunidades.filter(op => {
    const matchBusca = op.titulo?.toLowerCase().includes(busca.toLowerCase()) ||
      op.instituicao?.toLowerCase().includes(busca.toLowerCase())
    const matchTema = filtroTema ? (op.tematica === filtroTema || op.tematica?.toLowerCase().includes(filtroTema.toLowerCase())) : true
    const matchPrazo = filtroPrazo ? op.prazo === filtroPrazo : true

    return matchBusca && matchTema && matchPrazo
  })

  const aderenciaColor = (nivel) => {
    switch (nivel?.toLowerCase()) {
      case 'alto': return { bg: 'bg-emerald-500', text: 'text-emerald-500', border: 'border-emerald-500/50', glow: 'shadow-emerald-500/50' }
      case 'médio': return { bg: 'bg-amber-400', text: 'text-amber-400', border: 'border-amber-400/50', glow: 'shadow-amber-400/50' }
      case 'baixo': return { bg: 'bg-rose-500', text: 'text-rose-500', border: 'border-rose-500/50', glow: 'shadow-rose-500/50' }
      default: return { bg: 'bg-slate-500', text: 'text-slate-500', border: 'border-slate-500/50', glow: 'shadow-slate-500/50' }
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-cyan-500/30">
      {/* Modal CRUD de Temas */}
      <GerenciadorTemas
        isOpen={isModalTemasOpen}
        onClose={() => setIsModalTemasOpen(false)}
        onTemasAtualizados={(novos) => setTemasBanco(novos)}
      />

      <div className="max-w-7xl mx-auto px-4 py-12">

        {/* Header - Metro Style Signage */}
        <header className="mb-10 border-b-2 border-slate-800 pb-8 flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <img src={logo} alt="Logo NIT" className="h-12 w-auto" />
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white">
                Eventos de Inovação
              </h1>
            </div>
            <p className="text-slate-400 text-lg md:ml-15 font-medium tracking-wide">
              Buscador Automatizado • Oportunidades em exibição
            </p>
          </div>

          <div className="flex flex-col gap-3 w-full lg:w-auto">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Buscar edital ou instituição..."
                className="flex-1 lg:w-[320px] bg-slate-900 border border-slate-700 rounded-full py-3 px-5 text-slate-200 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder:text-slate-500 shadow-inner"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
              <button
                onClick={() => setIsModalTemasOpen(true)}
                className="bg-slate-900 hover:bg-slate-800 border border-cyan-500/50 hover:border-cyan-400 text-cyan-400 hover:text-white font-semibold py-3 px-4 rounded-full transition-all flex items-center gap-2 shadow-lg shadow-cyan-950/30 cursor-pointer text-sm whitespace-nowrap"
                title="Gerenciar temas e palavras-chave de interesse"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                <span>Temas</span>
                <span className="bg-cyan-500/20 text-cyan-300 text-xs px-2 py-0.5 rounded-full border border-cyan-500/30">
                  {temasBanco.length}
                </span>
              </button>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <select
                className="bg-slate-900 border border-slate-700 rounded-full py-2.5 px-4 text-sm text-slate-300 focus:outline-none focus:border-cyan-500 flex-1 appearance-none cursor-pointer"
                value={filtroTema}
                onChange={(e) => setFiltroTema(e.target.value)}
              >
                <option value="">Todos os Temas</option>
                {temasUnicos.map((tema, i) => <option key={i} value={tema}>{tema}</option>)}
              </select>
              <select
                className="bg-slate-900 border border-slate-700 rounded-full py-2.5 px-4 text-sm text-slate-300 focus:outline-none focus:border-cyan-500 flex-1 appearance-none cursor-pointer"
                value={filtroPrazo}
                onChange={(e) => setFiltroPrazo(e.target.value)}
              >
                <option value="">Todos os Prazos</option>
                {prazosUnicos.map((prazo, i) => <option key={i} value={prazo}>{prazo}</option>)}
              </select>
            </div>
          </div>
        </header>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="animate-pulse flex flex-col items-center gap-4">
              <div className="w-4 h-4 rounded-full bg-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.8)]"></div>
              <div className="text-cyan-500 font-semibold tracking-widest uppercase text-sm">Carregando sistema...</div>
            </div>
          </div>
        )}

        {/* Content - Grid of Cards */}
        {!loading && (
          <div>
            {filtradas.length === 0 ? (
              <div className="py-16 text-center text-slate-400 font-medium bg-slate-900/40 rounded-3xl border border-slate-800 border-dashed">
                Nenhuma oportunidade encontrada com os filtros atuais.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filtradas.map((op, index) => {
                  const colors = aderenciaColor(op.aderencia)
                  return (
                    <div key={op.id || index} className="group relative flex flex-col bg-slate-900/60 backdrop-blur-md border border-slate-800 p-7 rounded-3xl hover:border-slate-600 transition-all duration-300 hover:bg-slate-800/60 hover:shadow-2xl hover:shadow-cyan-900/10 hover:-translate-y-1">

                      {/* Top bar with category and aderência */}
                      <div className="flex items-center justify-between gap-2 mb-5">
                        <div className="flex items-center gap-2.5">
                          {/* Mini Node Icon to keep the Metro feel */}
                          <div className={`w-3.5 h-3.5 rounded-full ${colors.bg} shadow-md ${colors.glow}`}></div>
                          <span className="bg-slate-950 text-slate-300 text-xs font-bold px-2.5 py-1 rounded-md uppercase tracking-wider shadow-sm border border-slate-800">
                            {op.categoria}
                          </span>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-1 rounded-md border ${colors.border} ${colors.text} bg-slate-950/50 uppercase tracking-widest`}>
                          Aderência {op.aderencia}
                        </span>
                      </div>

                      <h2 className="text-xl font-bold text-white mb-3 leading-snug group-hover:text-cyan-400 transition-colors">
                        {op.titulo}
                      </h2>

                      <h3 className="text-cyan-500/80 font-medium mb-4 flex items-center gap-2 text-sm">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                        {op.instituicao}
                      </h3>

                      <p className="text-slate-400 mb-6 line-clamp-3 text-sm leading-relaxed flex-grow">
                        {op.resumo}
                      </p>

                      <div className="space-y-4 mt-auto pt-5 border-t border-slate-800/60">
                        <div className="flex flex-col gap-3">
                          <div className="flex items-center justify-between text-xs bg-slate-950/50 px-3 py-2 rounded-lg border border-slate-800">
                            <span className="text-slate-500 uppercase font-semibold">Tema</span>
                            <span className="text-slate-300 font-medium truncate max-w-[160px] ml-2" title={op.tematica}>{op.tematica}</span>
                          </div>
                          <div className="flex items-center justify-between text-xs bg-slate-950/50 px-3 py-2 rounded-lg border border-slate-800">
                            <span className="text-slate-500 uppercase font-semibold">Prazo</span>
                            <span className="text-slate-300 font-medium ml-2">{op.prazo || 'N/A'}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => setEditalSelecionado(op)}
                            className="flex items-center justify-center gap-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/40 hover:border-cyan-400 text-cyan-300 font-semibold px-3 py-2.5 rounded-xl transition-all text-xs cursor-pointer"
                            title="Exibir texto completo retido internamente no sistema"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                            Ver Conteúdo
                          </button>

                          <a
                            href={op.link}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center justify-center gap-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold px-3 py-2.5 rounded-xl transition-all text-xs hover:shadow-[0_0_12px_rgba(6,182,212,0.2)]"
                            title="Buscar edital no portal da FINEP via proxy seguro de busca do Google"
                          >
                            <span>FINEP (Busca)</span>
                            <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                          </a>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de Detalhes com Retenção de Conteúdo (descricaoRawText) */}
      {editalSelecionado && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl shadow-cyan-950/40 overflow-hidden">
            {/* Header do Modal */}
            <div className="p-6 border-b border-slate-800 flex items-start justify-between gap-4 bg-slate-900/90">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="bg-slate-950 text-cyan-400 border border-cyan-500/30 text-xs font-bold px-2.5 py-0.5 rounded-md uppercase tracking-wider">
                    {editalSelecionado.categoria}
                  </span>
                  <span className="text-xs text-slate-400">
                    • {editalSelecionado.instituicao}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${aderenciaColor(editalSelecionado.aderencia).border} ${aderenciaColor(editalSelecionado.aderencia).text} bg-slate-950/50 uppercase`}>
                    Aderência {editalSelecionado.aderencia}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-white leading-snug">
                  {editalSelecionado.titulo}
                </h2>
              </div>
              <button
                onClick={() => setEditalSelecionado(null)}
                className="text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 p-2 rounded-full transition-colors cursor-pointer"
                title="Fechar janela"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Corpo do Modal com Scroll */}
            <div className="p-6 overflow-y-auto space-y-6 text-sm">
              {/* Metadados rápidos */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-slate-950/60 p-4 rounded-2xl border border-slate-800">
                <div>
                  <span className="text-xs text-slate-500 uppercase font-semibold block">Tema / Palavra-chave</span>
                  <span className="text-slate-200 font-medium">{editalSelecionado.tematica || 'Geral'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase font-semibold block">Prazo</span>
                  <span className="text-slate-200 font-medium">{editalSelecionado.prazo || 'Consulte o texto'}</span>
                </div>
              </div>

              {/* Resumo Gerado pela IA */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 mb-2 flex items-center gap-1.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Resumo Analítico da IA
                </h3>
                <p className="text-slate-300 leading-relaxed bg-slate-950/40 p-4 rounded-2xl border border-slate-800/80">
                  {editalSelecionado.resumo}
                </p>
              </div>

              {/* Conteúdo Retido na Íntegra (descricaoRawText) */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Texto Completo Retido (Evita 404)
                  </h3>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {editalSelecionado.descricaoRawText ? `${editalSelecionado.descricaoRawText.length} caracteres` : 'Sem texto bruto'}
                  </span>
                </div>
                <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-4 max-h-72 overflow-y-auto font-sans text-xs text-slate-300 leading-relaxed whitespace-pre-line select-text">
                  {editalSelecionado.descricaoRawText || editalSelecionado.resumo || 'Nenhuma descrição detalhada disponível.'}
                </div>
              </div>
            </div>

            {/* Footer do Modal */}
            <div className="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between gap-4">
              <span className="text-xs text-slate-500 hidden sm:inline">
                Fonte: FINEP • Link via Proxy de Busca Google
              </span>
              <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                <button
                  onClick={() => setEditalSelecionado(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors cursor-pointer"
                >
                  Fechar
                </button>
                <a
                  href={editalSelecionado.link}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold text-white bg-cyan-600 hover:bg-cyan-500 transition-all shadow-lg shadow-cyan-900/40"
                >
                  <span>Buscar na FINEP (Google)</span>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App