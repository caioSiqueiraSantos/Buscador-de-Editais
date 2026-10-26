import { useEffect, useState, useMemo } from 'react'
import logo from './assets/NIT Logo.png'
import GerenciadorTemas from './components/GerenciadorTemas'
import ModalDescarte from './components/ModalDescarte'
import PainelAprendizadoIA from './components/PainelAprendizadoIA'
import { API_URL } from './config'

// Formatação determinística de datas para dd/mm/aaaa (Zero Alucinação)
const formatarDataBR = (dataRaw) => {
  if (!dataRaw || typeof dataRaw !== 'string') return dataRaw || 'Não informado'
  const texto = dataRaw.trim()
  if (!texto || texto.toLowerCase() === 'não informado' || texto.toLowerCase() === 'n/a') {
    return 'Não informado'
  }

  if (/^\d{2}\/\d{2}\/\d{4}$/.test(texto)) return texto

  const matchIso = texto.match(/^(\d{4})[-/](\d{2})[-/](\d{2})/)
  if (matchIso) {
    const [, ano, mes, dia] = matchIso
    return `${dia}/${mes}/${ano}`
  }

  const matchDmyHifen = texto.match(/^(\d{2})-(\d{2})-(\d{4})/)
  if (matchDmyHifen) {
    const [, dia, mes, ano] = matchDmyHifen
    return `${dia}/${mes}/${ano}`
  }

  const mesesMap = {
    janeiro: '01', fevereiro: '02', marco: '03', março: '03',
    abril: '04', maio: '05', junho: '06', julho: '07',
    agosto: '08', setembro: '09', outubro: '10', novembro: '11', dezembro: '12',
    jan: '01', fev: '02', mar: '03', abr: '04', mai: '05', jun: '06',
    jul: '07', ago: '08', set: '09', out: '10', nov: '11', dez: '12'
  }

  const matchExtenso = texto.toLowerCase().match(/(\d{1,2})(?:º|o)?\s+de\s+([a-zç]+)\s+de\s+(\d{4})/)
  if (matchExtenso) {
    const dia = matchExtenso[1].padStart(2, '0')
    const nomeMes = matchExtenso[2].normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    const mes = mesesMap[nomeMes]
    const ano = matchExtenso[3]
    if (mes) return `${dia}/${mes}/${ano}`
  }

  const matchDataEmbutidaIso = texto.match(/(\d{4})[-/](\d{2})[-/](\d{2})/)
  if (matchDataEmbutidaIso) {
    const [, ano, mes, dia] = matchDataEmbutidaIso
    return `${dia}/${mes}/${ano}`
  }
  const matchDataEmbutidaBr = texto.match(/(\d{2})\/(\d{2})\/(\d{4})/)
  if (matchDataEmbutidaBr) {
    return matchDataEmbutidaBr[0]
  }

  return texto
}

function App() {
  const [oportunidades, setOportunidades] = useState([])
  const [busca, setBusca] = useState("")
  const [filtroTema, setFiltroTema] = useState("")
  const [filtroPrazo, setFiltroPrazo] = useState("")
  const [filtroAderencia, setFiltroAderencia] = useState("")
  const [filtroRevisao, setFiltroRevisao] = useState("") // "" | "revisado" | "pendente"
  const [incluirDescartados, setIncluirDescartados] = useState(false)

  const [loading, setLoading] = useState(true)
  const [temasBanco, setTemasBanco] = useState([])
  const [statsIA, setStatsIA] = useState(null)

  // Modais
  const [isModalTemasOpen, setIsModalTemasOpen] = useState(false)
  const [isModalAprendizadoOpen, setIsModalAprendizadoOpen] = useState(false)
  const [editalDescarteAlvo, setEditalDescarteAlvo] = useState(null)
  const [editalSelecionado, setEditalSelecionado] = useState(null)

  // Toast de feedback
  const [toast, setToast] = useState(null)

  const showToast = (mensagem, tipo = 'sucesso') => {
    setToast({ mensagem, tipo })
    setTimeout(() => setToast(null), 4500)
  }

  const carregarOportunidades = () => {
    setLoading(true)
    const url = `${API_URL}/oportunidades?incluir_descartados=${incluirDescartados}`
    fetch(url)
      .then(response => response.json())
      .then(data => {
        const dadosNormalizados = Array.isArray(data)
          ? data.map(op => ({
            ...op,
            prazo: formatarDataBR(op.prazo),
            aderencia_efetiva: op.aderencia_humana || op.aderencia
          }))
          : []
        setOportunidades(dadosNormalizados)
        setLoading(false)
      })
      .catch(error => {
        console.error("Erro ao buscar dados:", error)
        setLoading(false)
      })
  }

  const carregarTemasBanco = () => {
    fetch(`${API_URL}/temas`)
      .then(response => response.json())
      .then(data => setTemasBanco(Array.isArray(data) ? data : []))
      .catch(error => console.error("Erro ao buscar temas:", error))
  }

  const carregarEstatisticasIA = () => {
    fetch(`${API_URL}/ia/aprendizado`)
      .then(response => response.json())
      .then(data => setStatsIA(data?.metricas || null))
      .catch(error => console.error("Erro ao buscar estatísticas da IA:", error))
  }

  useEffect(() => {
    carregarOportunidades()
  }, [incluirDescartados])

  useEffect(() => {
    carregarTemasBanco()
    carregarEstatisticasIA()
  }, [])

  // Ações de Calibração Human-in-the-Loop
  const handleCalibrarAderencia = async (opId, novaAderencia, motivo = null) => {
    try {
      const res = await fetch(`${API_URL}/oportunidades/${opId}/aderencia`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          aderencia: novaAderencia,
          motivo: motivo || `Calibrado manualmente para ${novaAderencia} pela equipe técnica`
        })
      })

      if (!res.ok) throw new Error('Falha ao calibrar aderência.')
      const data = await res.json()

      // Atualiza estado local imediatamente
      setOportunidades(prev => prev.map(op => {
        if (op.id === opId) {
          return {
            ...op,
            aderencia_humana: novaAderencia,
            aderencia_efetiva: novaAderencia,
            revisado_por_humano: true,
            status_revisao: 'ajustado',
            motivo_feedback: data.oportunidade?.motivo_feedback
          }
        }
        return op
      }))

      if (editalSelecionado && editalSelecionado.id === opId) {
        setEditalSelecionado(prev => ({
          ...prev,
          aderencia_humana: novaAderencia,
          aderencia_efetiva: novaAderencia,
          revisado_por_humano: true,
          status_revisao: 'ajustado',
          motivo_feedback: data.oportunidade?.motivo_feedback
        }))
      }

      showToast(`Aderência calibrada para "${novaAderencia}"! A IA foi treinada com este exemplo.`)
      carregarEstatisticasIA()
    } catch (err) {
      console.error(err)
      showToast('Erro ao atualizar aderência.', 'erro')
    }
  }

  const handleDescartarEdital = async (opId, motivo) => {
    try {
      const res = await fetch(`${API_URL}/oportunidades/${opId}/descartar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ motivo })
      })

      if (!res.ok) throw new Error('Falha ao descartar edital.')

      if (incluirDescartados) {
        setOportunidades(prev => prev.map(op => op.id === opId ? { ...op, excluido: true, status_revisao: 'descartado', motivo_feedback: motivo } : op))
      } else {
        setOportunidades(prev => prev.filter(op => op.id !== opId))
      }

      if (editalSelecionado && editalSelecionado.id === opId) {
        setEditalSelecionado(null)
      }

      showToast('Edital descartado e registrado na memória de falsos positivos da IA!')
      carregarEstatisticasIA()
    } catch (err) {
      console.error(err)
      showToast('Erro ao descartar edital.', 'erro')
    }
  }

  // Extração de valores únicos para os filtros
  const temasUnicos = useMemo(() => {
    const temasOps = oportunidades.map(op => op.tematica).filter(Boolean)
    const temasDb = temasBanco.map(t => t.nome).filter(Boolean)
    return [...new Set([...temasOps, ...temasDb])].sort()
  }, [oportunidades, temasBanco])

  const prazosUnicos = useMemo(() => {
    const prazos = oportunidades.map(op => op.prazo).filter(Boolean)
    return [...new Set(prazos)].sort((a, b) => {
      const matchA = a.match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
      const matchB = b.match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
      if (matchA && matchB) {
        const valA = `${matchA[3]}${matchA[2]}${matchA[1]}`
        const valB = `${matchB[3]}${matchB[2]}${matchB[1]}`
        return valA.localeCompare(valB)
      }
      return a.localeCompare(b)
    })
  }, [oportunidades])

  const filtradas = oportunidades.filter(op => {
    const matchBusca = op.titulo?.toLowerCase().includes(busca.toLowerCase()) ||
      op.instituicao?.toLowerCase().includes(busca.toLowerCase())
    const matchTema = filtroTema ? (op.tematica === filtroTema || op.tematica?.toLowerCase().includes(filtroTema.toLowerCase())) : true
    const matchPrazo = filtroPrazo ? op.prazo === filtroPrazo : true

    // Filtro por aderência efetiva (humana se existir, senão IA)
    const nivelEfetivo = (op.aderencia_efetiva || op.aderencia || '').toLowerCase()
    const matchAderencia = filtroAderencia
      ? (nivelEfetivo === filtroAderencia.toLowerCase() ||
        (filtroAderencia === 'Médio' && nivelEfetivo === 'medio'))
      : true

    // Filtro por status de revisão humana
    let matchRevisao = true
    if (filtroRevisao === 'revisado') {
      matchRevisao = op.revisado_por_humano === true
    } else if (filtroRevisao === 'pendente') {
      matchRevisao = !op.revisado_por_humano
    }

    return matchBusca && matchTema && matchPrazo && matchAderencia && matchRevisao
  })

  const aderenciaColor = (nivel) => {
    switch (nivel?.toLowerCase()) {
      case 'alto': return { bg: 'bg-emerald-500', text: 'text-emerald-400', border: 'border-emerald-500/50', glow: 'shadow-emerald-500/40', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' }
      case 'médio':
      case 'medio': return { bg: 'bg-amber-400', text: 'text-amber-400', border: 'border-amber-400/50', glow: 'shadow-amber-400/40', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30' }
      case 'baixo': return { bg: 'bg-rose-500', text: 'text-rose-400', border: 'border-rose-500/50', glow: 'shadow-rose-500/40', badge: 'bg-rose-500/10 text-rose-400 border-rose-500/30' }
      default: return { bg: 'bg-slate-500', text: 'text-slate-400', border: 'border-slate-500/50', glow: 'shadow-slate-500/40', badge: 'bg-slate-500/10 text-slate-400 border-slate-500/30' }
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-cyan-500/30">

      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 py-3 px-5 rounded-2xl shadow-2xl backdrop-blur-md border flex items-center gap-3 animate-in fade-in slide-in-from-bottom-5 duration-300 text-xs font-semibold ${toast.tipo === 'erro'
          ? 'bg-rose-950/90 border-rose-500/50 text-rose-200 shadow-rose-950/50'
          : 'bg-cyan-950/90 border-cyan-500/50 text-cyan-200 shadow-cyan-950/50'
          }`}>
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
          <span>{toast.mensagem}</span>
        </div>
      )}

      {/* Modal CRUD de Temas */}
      <GerenciadorTemas
        isOpen={isModalTemasOpen}
        onClose={() => setIsModalTemasOpen(false)}
        onTemasAtualizados={(novos) => setTemasBanco(novos)}
      />

      {/* Modal de Aprendizado da IA (Human-in-the-Loop) */}
      <PainelAprendizadoIA
        isOpen={isModalAprendizadoOpen}
        onClose={() => setIsModalAprendizadoOpen(false)}
        onOportunidadeRestaurada={() => {
          carregarOportunidades()
          carregarEstatisticasIA()
        }}
      />

      {/* Modal de Descarte de Edital */}
      <ModalDescarte
        isOpen={!!editalDescarteAlvo}
        onClose={() => setEditalDescarteAlvo(null)}
        edital={editalDescarteAlvo}
        onDescartar={handleDescartarEdital}
      />

      <div className="max-w-7xl mx-auto px-4 py-12">

        {/* Header - Metro Style Signage */}
        <header className="mb-10 border-b-2 border-slate-800 pb-8 flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <img src={logo} alt="Logo NIT" className="h-12 w-auto shrink-0" />
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white">
                Inovação
              </h1>
            </div>
            <p className="text-slate-400 text-lg md:ml-15 font-medium tracking-wide flex items-center gap-2 flex-wrap">
              <span>Buscador & Triagem Inteligente</span>
              <span>•</span>
              {!loading ? (
                <span className="text-cyan-400 font-semibold inline-flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shrink-0"></span>
                  {filtradas.length} {filtradas.length === 1 ? 'oportunidade' : 'oportunidades'}
                  {oportunidades.length > 0 && filtradas.length !== oportunidades.length && (
                    <span className="text-slate-500 font-normal text-sm">
                      (de {oportunidades.length} no total)
                    </span>
                  )}
                </span>
              ) : (
                <span className="text-slate-500">Carregando sistema...</span>
              )}
            </p>
          </div>

          <div className="flex flex-col gap-3 w-full lg:w-auto">
            {/* Linha Superior de Ações: Busca + Botão Temas + Botão Memória IA */}
            <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
              <input
                type="text"
                placeholder="Buscar edital ou instituição..."
                className="flex-1 min-w-[200px] lg:w-[280px] bg-slate-900 border border-slate-700 rounded-full py-3 px-5 text-slate-200 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder:text-slate-500 shadow-inner text-sm"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />

              <button
                onClick={() => setIsModalTemasOpen(true)}
                className="bg-slate-900 hover:bg-slate-800 border border-cyan-500/50 hover:border-cyan-400 text-cyan-400 hover:text-white font-semibold py-3 px-4 rounded-full transition-all flex items-center gap-2 shadow-lg shadow-cyan-950/30 cursor-pointer text-xs whitespace-nowrap"
                title="Gerenciar temas e palavras-chave do Metrô"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                <span>Temas</span>
                <span className="bg-cyan-500/20 text-cyan-300 text-[10px] px-1.5 py-0.5 rounded-full border border-cyan-500/30">
                  {temasBanco.length}
                </span>
              </button>

              {/* Botão Novo: Memória da IA */}
              <button
                onClick={() => setIsModalAprendizadoOpen(true)}
                className="bg-gradient-to-r from-indigo-900/60 to-cyan-900/60 hover:from-indigo-800/80 hover:to-cyan-800/80 border border-indigo-500/50 hover:border-cyan-400 text-cyan-300 hover:text-white font-semibold py-3 px-4 rounded-full transition-all flex items-center gap-2 shadow-lg shadow-indigo-950/40 cursor-pointer text-xs whitespace-nowrap"
                title="Visualizar o painel de calibragem e memória de aprendizado contínuo da IA"
              >
                <span>Memória</span>
                {statsIA?.total_calibradas_humano > 0 && (
                  <span className="bg-emerald-500/20 text-emerald-300 text-[10px] font-bold px-1.5 py-0.5 rounded-full border border-emerald-500/30">
                    {statsIA.total_calibradas_humano} calibrados
                  </span>
                )}
              </button>
            </div>

            {/* Linha de Filtros Selects */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <select
                className="bg-slate-900 border border-slate-700 rounded-full py-2 px-3 text-xs text-slate-300 focus:outline-none focus:border-cyan-500 cursor-pointer"
                value={filtroTema}
                onChange={(e) => setFiltroTema(e.target.value)}
              >
                <option value="">Todos os Temas</option>
                {temasUnicos.map((tema, i) => <option key={i} value={tema}>{tema}</option>)}
              </select>

              <select
                className="bg-slate-900 border border-slate-700 rounded-full py-2 px-3 text-xs text-slate-300 focus:outline-none focus:border-cyan-500 cursor-pointer"
                value={filtroPrazo}
                onChange={(e) => setFiltroPrazo(e.target.value)}
              >
                <option value="">Todos os Prazos</option>
                {prazosUnicos.map((prazo, i) => <option key={i} value={prazo}>{prazo}</option>)}
              </select>

              <select
                className="bg-slate-900 border border-slate-700 rounded-full py-2 px-3 text-xs text-slate-300 focus:outline-none focus:border-cyan-500 cursor-pointer"
                value={filtroAderencia}
                onChange={(e) => setFiltroAderencia(e.target.value)}
              >
                <option value="">Todas as Aderências</option>
                <option value="Alto">Aderência Alta</option>
                <option value="Médio">Aderência Média</option>
                <option value="Baixo">Aderência Baixa</option>
              </select>

              <select
                className="bg-slate-900 border border-slate-700 rounded-full py-2 px-3 text-xs text-slate-300 focus:outline-none focus:border-cyan-500 cursor-pointer"
                value={filtroRevisao}
                onChange={(e) => setFiltroRevisao(e.target.value)}
              >
                <option value="">Status de Revisão</option>
                <option value="revisado">✓ Revisado por Humano</option>
                <option value="pendente">✦ Sugerido por IA</option>
              </select>
            </div>

            {/* Toggle de Descartados */}
            <div className="flex items-center justify-end gap-2 text-xs text-slate-400 pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none hover:text-slate-200 transition-colors">
                <input
                  type="checkbox"
                  checked={incluirDescartados}
                  onChange={(e) => setIncluirDescartados(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500 cursor-pointer"
                />
                <span>Exibir editais descartados</span>
              </label>
            </div>
          </div>
        </header>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="animate-pulse flex flex-col items-center gap-4">
              <div className="w-4 h-4 rounded-full bg-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.8)]"></div>
              <div className="text-cyan-500 font-semibold tracking-widest uppercase text-sm">Carregando oportunidades...</div>
            </div>
          </div>
        )}

        {/* Content - Grid of Cards */}
        {!loading && (
          <div>
            {filtradas.length === 0 ? (
              <div className="py-16 text-center text-slate-400 font-medium bg-slate-900/40 rounded-3xl border border-slate-800 border-dashed">
                Nenhuma oportunidade encontrada com os filtros selecionados.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filtradas.map((op, index) => {
                  const nivelEfetivo = op.aderencia_efetiva || op.aderencia
                  const colors = aderenciaColor(nivelEfetivo)
                  const isDescartado = Boolean(op.excluido)

                  return (
                    <div
                      key={op.id || index}
                      className={`group relative flex flex-col bg-slate-900/60 backdrop-blur-md border p-6 rounded-3xl transition-all duration-300 hover:shadow-2xl hover:shadow-cyan-900/10 hover:-translate-y-1 ${isDescartado
                        ? 'border-rose-900/50 bg-rose-950/10 opacity-70'
                        : 'border-slate-800 hover:border-slate-600 hover:bg-slate-800/60'
                        }`}
                    >
                      {/* Top bar with category, aderência e botão de descarte */}
                      <div className="flex items-center justify-between gap-2 mb-4">
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${colors.bg} shadow-md ${colors.glow}`}></div>
                          <span className="bg-slate-950 text-slate-300 text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider border border-slate-800">
                            {op.categoria}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5">
                          {/* Badge de Aderência com distinção Humano x IA */}
                          <span
                            className={`text-[10px] font-bold px-2 py-1 rounded-md border uppercase tracking-wider flex items-center gap-1 ${op.revisado_por_humano
                              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40'
                              : `${colors.badge}`
                              }`}
                            title={op.revisado_por_humano ? 'Calibrado por especialista humano' : 'Classificado preliminarmente pela IA'}
                          >
                            {op.revisado_por_humano ? '✓' : '✦'} {nivelEfetivo}
                          </span>

                          {/* Botão de Descarte / Lixeira */}
                          {!isDescartado ? (
                            <button
                              onClick={() => setEditalDescarteAlvo(op)}
                              className="text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 p-1.5 rounded-lg transition-colors cursor-pointer"
                              title="Descartar edital e treinar a IA com falso positivo"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          ) : (
                            <span className="bg-rose-500/20 text-rose-300 text-[9px] font-bold px-1.5 py-0.5 rounded border border-rose-500/30 uppercase">
                              Descartado
                            </span>
                          )}
                        </div>
                      </div>

                      <h2 className="text-lg font-bold text-white mb-2 leading-snug group-hover:text-cyan-400 transition-colors line-clamp-2">
                        {op.titulo}
                      </h2>

                      <h3 className="text-cyan-500/80 font-medium mb-3 flex items-center gap-1.5 text-xs">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                        {op.instituicao}
                      </h3>

                      <p className="text-slate-400 mb-5 line-clamp-3 text-xs leading-relaxed flex-grow">
                        {op.resumo}
                      </p>

                      {/* Calibração Rápida de Aderência (Human-in-the-Loop Inline) */}
                      {!isDescartado && (
                        <div className="mb-4 bg-slate-950/70 p-2.5 rounded-2xl border border-slate-800/80">
                          <div className="flex items-center justify-between text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1.5 px-1">
                            <span>Calibrar Aderência:</span>
                            <span className="text-[9px] text-slate-500 font-normal">Treina a IA</span>
                          </div>
                          <div className="grid grid-cols-3 gap-1">
                            {['Alto', 'Médio', 'Baixo'].map((nivel) => {
                              const isAtivo = nivelEfetivo?.toLowerCase() === nivel.toLowerCase() ||
                                (nivel === 'Médio' && nivelEfetivo?.toLowerCase() === 'medio')
                              const btnColor = aderenciaColor(nivel)
                              return (
                                <button
                                  key={nivel}
                                  onClick={() => handleCalibrarAderencia(op.id, nivel)}
                                  className={`py-1 px-1.5 rounded-lg text-[10px] font-bold transition-all cursor-pointer text-center ${isAtivo
                                    ? `${btnColor.bg} text-slate-950 shadow-md ${btnColor.glow}`
                                    : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800'
                                    }`}
                                >
                                  {nivel}
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      )}

                      <div className="space-y-3 mt-auto pt-4 border-t border-slate-800/60">
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center justify-between text-[11px] bg-slate-950/50 px-3 py-1.5 rounded-lg border border-slate-800">
                            <span className="text-slate-500 uppercase font-semibold">Tema</span>
                            <span className="text-slate-300 font-medium truncate max-w-[150px] ml-2" title={op.tematica}>{op.tematica}</span>
                          </div>
                          <div className="flex items-center justify-between text-[11px] bg-slate-950/50 px-3 py-1.5 rounded-lg border border-slate-800">
                            <span className="text-slate-500 uppercase font-semibold">Prazo</span>
                            <span className="text-slate-300 font-medium ml-2">{op.prazo || 'N/A'}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2 pt-1">
                          <button
                            onClick={() => setEditalSelecionado(op)}
                            className="flex items-center justify-center gap-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/40 hover:border-cyan-400 text-cyan-300 font-semibold px-3 py-2 rounded-xl transition-all text-xs cursor-pointer"
                            title="Exibir texto completo retido e auditoria de IA"
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
                            className="flex items-center justify-center gap-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold px-3 py-2 rounded-xl transition-all text-xs hover:shadow-[0_0_12px_rgba(6,182,212,0.2)]"
                          >
                            <span>FINEP</span>
                            <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

      {/* Modal de Detalhes com Retenção de Conteúdo & Auditoria de IA */}
      {editalSelecionado && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl shadow-cyan-950/40 overflow-hidden">

            {/* Header do Modal */}
            <div className="p-6 border-b border-slate-800 flex items-start justify-between gap-4 bg-slate-900/90">
              <div>
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className="bg-slate-950 text-cyan-400 border border-cyan-500/30 text-xs font-bold px-2.5 py-0.5 rounded-md uppercase tracking-wider">
                    {editalSelecionado.categoria}
                  </span>
                  <span className="text-xs text-slate-400">
                    • {editalSelecionado.instituicao}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${aderenciaColor(editalSelecionado.aderencia_efetiva).border} ${aderenciaColor(editalSelecionado.aderencia_efetiva).text} bg-slate-950/50 uppercase`}>
                    Aderência {editalSelecionado.aderencia_efetiva} {editalSelecionado.revisado_por_humano ? '(Validado por Humano)' : '(Sugerido pela IA)'}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-white leading-snug">
                  {editalSelecionado.titulo}
                </h2>
              </div>
              <button
                onClick={() => setEditalSelecionado(null)}
                className="text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 p-2 rounded-full transition-colors cursor-pointer"
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

              {/* Seção Nova: Auditoria e Calibração de IA (Human-in-the-Loop) */}
              <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950/30 p-5 rounded-2xl border border-indigo-500/30 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                    <span>🧠</span> Auditoria e Calibração da IA
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${editalSelecionado.revisado_por_humano
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    }`}>
                    {editalSelecionado.revisado_por_humano ? 'Revisado por Especialista' : 'Aguardando Validação'}
                  </span>
                </div>

                <div className="text-xs text-slate-300 space-y-1">
                  <p>
                    <strong className="text-slate-400">Classificação Original da IA:</strong> {editalSelecionado.aderencia}
                  </p>
                  {editalSelecionado.justificativa_ia && (
                    <p className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800 text-slate-300 italic">
                      "{editalSelecionado.justificativa_ia}"
                    </p>
                  )}
                  {editalSelecionado.motivo_feedback && (
                    <p className="text-emerald-400 mt-1">
                      <strong>Observação do Especialista:</strong> {editalSelecionado.motivo_feedback}
                    </p>
                  )}
                </div>

                {/* Seletor de calibração dentro do modal */}
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between flex-wrap gap-2">
                  <span className="text-xs text-slate-400 font-medium">Reclassificar aderência:</span>
                  <div className="flex gap-2">
                    {['Alto', 'Médio', 'Baixo'].map((nivel) => (
                      <button
                        key={nivel}
                        onClick={() => handleCalibrarAderencia(editalSelecionado.id, nivel)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${(editalSelecionado.aderencia_efetiva || '').toLowerCase() === nivel.toLowerCase()
                          ? `${aderenciaColor(nivel).bg} text-slate-950 shadow-md`
                          : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                          }`}
                      >
                        {nivel}
                      </button>
                    ))}
                  </div>
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
                    Texto Completo Retido
                  </h3>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {editalSelecionado.descricaoRawText ? `${editalSelecionado.descricaoRawText.length} caracteres` : 'Sem texto bruto'}
                  </span>
                </div>
                <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-4 max-h-60 overflow-y-auto font-sans text-xs text-slate-300 leading-relaxed whitespace-pre-line select-text">
                  {editalSelecionado.descricaoRawText || editalSelecionado.resumo || 'Nenhuma descrição detalhada disponível.'}
                </div>
              </div>
            </div>

            {/* Footer do Modal */}
            <div className="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between gap-4">
              <button
                onClick={() => {
                  setEditalDescarteAlvo(editalSelecionado)
                  setEditalSelecionado(null)
                }}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold text-rose-400 hover:text-white bg-rose-950/30 hover:bg-rose-900/50 border border-rose-900/50 transition-colors cursor-pointer flex items-center gap-1.5"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span>Descartar Edital</span>
              </button>

              <div className="flex items-center gap-3">
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
                  <span>Portal FINEP</span>
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