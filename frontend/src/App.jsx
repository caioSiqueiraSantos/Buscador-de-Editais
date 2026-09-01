import { useEffect, useState } from 'react'

function App() {
  const [oportunidades, setOportunidades] = useState([])
  const [busca, setBusca] = useState("")
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

  const filtradas = oportunidades.filter(op =>
    op.titulo.toLowerCase().includes(busca.toLowerCase()) ||
    op.tematica.toLowerCase().includes(busca.toLowerCase()) ||
    op.instituicao.toLowerCase().includes(busca.toLowerCase())
  )

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
      <div className="max-w-5xl mx-auto px-4 py-12">
        
        {/* Header - Metro Style Signage */}
        <header className="mb-12 border-b-2 border-slate-800 pb-8 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-full bg-cyan-500 flex items-center justify-center font-bold text-slate-950 text-2xl shadow-[0_0_20px_rgba(6,182,212,0.6)]">
                M
              </div>
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white">
                Linha de Inovação
              </h1>
            </div>
            <p className="text-slate-400 text-lg md:ml-15 font-medium tracking-wide">
              Buscador Automatizado • Próxima parada: Oportunidades
            </p>
          </div>
          
          <div className="relative w-full md:w-96">
            <input
              type="text"
              placeholder="Buscar estação, tema ou edital..."
              className="w-full bg-slate-900 border border-slate-700 rounded-full py-3.5 px-6 text-slate-200 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder:text-slate-500 shadow-inner"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
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

        {/* Content - Route Map */}
        {!loading && (
          <div className="relative pl-4 md:pl-10">
            {/* Main Metro Line */}
            <div className="absolute left-8 md:left-14 top-8 bottom-8 w-2 bg-slate-800 rounded-full"></div>

            {filtradas.length === 0 ? (
              <div className="py-12 pl-12 text-slate-400 font-medium">
                Nenhuma oportunidade encontrada nesta rota.
              </div>
            ) : (
              <div className="flex flex-col gap-10">
                {filtradas.map((op, index) => {
                  const colors = aderenciaColor(op.aderencia)
                  return (
                    <div key={op.id || index} className="relative flex items-start group">
                      
                      {/* Station Node */}
                      <div className="absolute -left-4 md:-left-4 mt-3 z-10 flex items-center justify-center">
                        <div className={`w-8 h-8 rounded-full border-4 border-slate-950 ${colors.bg} shadow-lg ${colors.glow} flex items-center justify-center transition-transform group-hover:scale-125 duration-300`}>
                        </div>
                      </div>

                      {/* Card Content */}
                      <div className="ml-12 md:ml-16 bg-slate-900/40 backdrop-blur-md border border-slate-800/80 p-6 md:p-8 rounded-3xl w-full hover:border-slate-600 transition-all duration-300 hover:bg-slate-800/50 hover:shadow-2xl hover:shadow-cyan-900/10">
                        <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                          <div className="flex items-center gap-3">
                            <span className="bg-slate-800 text-slate-200 text-xs font-bold px-3 py-1.5 rounded-lg uppercase tracking-wider shadow-sm">
                              {op.categoria}
                            </span>
                            <span className={`text-xs font-bold px-3 py-1.5 rounded-lg border ${colors.border} ${colors.text} bg-slate-950/50 shadow-sm`}>
                              ADERÊNCIA {op.aderencia?.toUpperCase()}
                            </span>
                          </div>
                          <span className="text-slate-400 text-sm font-medium bg-slate-950/50 px-4 py-1.5 rounded-full border border-slate-800">
                            Prazo: {op.prazo || 'N/A'}
                          </span>
                        </div>
                        
                        <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-3 leading-tight group-hover:text-cyan-400 transition-colors">
                          {op.titulo}
                        </h2>
                        
                        <h3 className="text-cyan-500 font-semibold mb-5 flex items-center gap-2 text-lg">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                          {op.instituicao}
                        </h3>
                        
                        <p className="text-slate-300 mb-8 line-clamp-3 text-base md:text-lg leading-relaxed">
                          {op.resumo}
                        </p>

                        <div className="flex flex-wrap items-center justify-between gap-4 mt-auto pt-5 border-t border-slate-800/60">
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500 uppercase tracking-widest font-bold">Tema</span>
                            <span className="text-sm text-slate-300 font-semibold px-3 py-1.5 bg-slate-800/50 rounded-lg border border-slate-700/50">
                              {op.tematica}
                            </span>
                          </div>
                          
                          <a 
                            href={op.link} 
                            target="_blank" 
                            rel="noreferrer"
                            className="inline-flex items-center gap-2 bg-slate-100 hover:bg-white text-slate-900 font-bold px-6 py-3 rounded-xl transition-all hover:shadow-[0_0_20px_rgba(255,255,255,0.4)] hover:-translate-y-1 active:translate-y-0"
                          >
                            Embarcar
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
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
    </div>
  )
}

export default App