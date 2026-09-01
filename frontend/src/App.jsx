import { useEffect, useState, useMemo } from 'react'
import logo from './assets/NIT Logo.png';

function App() {
  const [oportunidades, setOportunidades] = useState([])
  const [busca, setBusca] = useState("")
  const [filtroTema, setFiltroTema] = useState("")
  const [filtroPrazo, setFiltroPrazo] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
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
  }, [])

  // Extração de valores únicos para os filtros
  const temasUnicos = useMemo(() => {
    const temas = oportunidades.map(op => op.tematica).filter(Boolean)
    return [...new Set(temas)].sort()
  }, [oportunidades])

  const prazosUnicos = useMemo(() => {
    const prazos = oportunidades.map(op => op.prazo).filter(Boolean)
    return [...new Set(prazos)].sort()
  }, [oportunidades])

  const filtradas = oportunidades.filter(op => {
    const matchBusca = op.titulo?.toLowerCase().includes(busca.toLowerCase()) ||
      op.instituicao?.toLowerCase().includes(busca.toLowerCase())
    const matchTema = filtroTema ? op.tematica === filtroTema : true
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
            <input
              type="text"
              placeholder="Buscar edital ou instituição..."
              className="w-full lg:w-[400px] bg-slate-900 border border-slate-700 rounded-full py-3 px-5 text-slate-200 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder:text-slate-500 shadow-inner"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
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

                        <a
                          href={op.link}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center justify-center gap-2 w-full bg-slate-800 hover:bg-slate-700 text-white font-bold px-4 py-3 rounded-xl transition-all hover:shadow-[0_0_15px_rgba(255,255,255,0.15)]"
                        >
                          Acessar Estação
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                        </a>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App