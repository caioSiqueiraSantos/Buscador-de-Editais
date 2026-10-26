import { useState, useEffect } from 'react'
import { API_URL } from '../config'

export default function PainelAprendizadoIA({ isOpen, onClose, onOportunidadeRestaurada }) {
  const [metricas, setMetricas] = useState(null)
  const [exemplos, setExemplos] = useState({ positivos_referencia: [], negativos_falsos_positivos: [] })
  const [descartados, setDescartados] = useState([])
  const [abaAtiva, setAbaAtiva] = useState('metricas') // 'metricas' | 'positivos' | 'descartados' | 'como_funciona'
  const [loading, setLoading] = useState(true)
  const [restaurandoId, setRestaurandoId] = useState(null)
  const [mensagemSucesso, setMensagemSucesso] = useState('')

  const carregarDadosIA = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_URL}/ia/aprendizado`)
      if (res.ok) {
        const data = await res.json()
        setMetricas(data.metricas)
        setExemplos(data.exemplos_ativos_injetados_na_ia || {})
      }

      // Carregar lista completa de descartados para poder restaurar
      const resDesc = await fetch(`${API_URL}/oportunidades?incluir_descartados=true&status_revisao=descartado`)
      if (resDesc.ok) {
        const dataDesc = await resDesc.json()
        setDescartados(dataDesc)
      }
    } catch (err) {
      console.error('Erro ao carregar dados do aprendizado:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      carregarDadosIA()
      setMensagemSucesso('')
    }
  }, [isOpen])

  const handleRestaurar = async (id) => {
    try {
      setRestaurandoId(id)
      const res = await fetch(`${API_URL}/oportunidades/${id}/restaurar`, {
        method: 'POST'
      })
      if (res.ok) {
        setMensagemSucesso('Oportunidade restaurada para a lista ativa com sucesso!')
        await carregarDadosIA()
        if (onOportunidadeRestaurada) {
          onOportunidadeRestaurada()
        }
      }
    } catch (err) {
      console.error('Erro ao restaurar:', err)
    } finally {
      setRestaurandoId(null)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700 rounded-3xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl shadow-cyan-950/30 overflow-hidden">
        
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between gap-4 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-900/40 shrink-0">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white">Memória e Aprendizado da IA</h2>
                <span className="bg-cyan-500/20 text-cyan-300 text-[10px] font-bold px-2 py-0.5 rounded-full border border-cyan-500/30 uppercase tracking-wider">
                  Human-in-the-Loop
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Como as calibrações de aderência e exclusões dos especialistas orientam as futuras buscas do Gemini
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 p-2 rounded-full transition-colors cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Sub-header Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 px-6 gap-2 overflow-x-auto">
          <button
            onClick={() => setAbaAtiva('metricas')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              abaAtiva === 'metricas'
                ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            📊 Painel de Métricas
          </button>
          <button
            onClick={() => setAbaAtiva('positivos')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              abaAtiva === 'positivos'
                ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🎯 Exemplos Validados ({exemplos.positivos_referencia?.length || 0})
          </button>
          <button
            onClick={() => setAbaAtiva('descartados')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              abaAtiva === 'descartados'
                ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🚫 Falsos Positivos Descartados ({descartados.length})
          </button>
          <button
            onClick={() => setAbaAtiva('como_funciona')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              abaAtiva === 'como_funciona'
                ? 'border-cyan-400 text-cyan-400 bg-cyan-950/20'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            ⚡ Como a IA Aprende
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm">
          {mensagemSucesso && (
            <div className="bg-emerald-950/30 border border-emerald-500/40 text-emerald-300 p-3 rounded-2xl text-xs flex items-center justify-between">
              <span>{mensagemSucesso}</span>
              <button onClick={() => setMensagemSucesso('')} className="text-emerald-400 hover:text-emerald-200 font-bold ml-2">✕</button>
            </div>
          )}

          {loading ? (
            <div className="py-16 text-center text-slate-400 animate-pulse">
              Carregando dados da memória de IA...
            </div>
          ) : (
            <>
              {/* ABA 1: MÉTRICAS */}
              {abaAtiva === 'metricas' && metricas && (
                <div className="space-y-6">
                  {/* Cards de Métricas Rápidas */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-2xl">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                        Editais Ativos
                      </span>
                      <span className="text-2xl font-extrabold text-white">
                        {metricas.total_ativas}
                      </span>
                    </div>

                    <div className="bg-slate-950/60 border border-emerald-500/30 p-4 rounded-2xl">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block mb-1">
                        Calibrados por Humano
                      </span>
                      <span className="text-2xl font-extrabold text-emerald-400">
                        {metricas.total_calibradas_humano}
                      </span>
                    </div>

                    <div className="bg-slate-950/60 border border-rose-500/30 p-4 rounded-2xl">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400 block mb-1">
                        Falsos Positivos Descartados
                      </span>
                      <span className="text-2xl font-extrabold text-rose-400">
                        {metricas.total_falsos_positivos_descartados}
                      </span>
                    </div>

                    <div className="bg-slate-950/60 border border-cyan-500/30 p-4 rounded-2xl">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block mb-1">
                        Concordância IA x Humano
                      </span>
                      <span className="text-2xl font-extrabold text-cyan-400">
                        {metricas.taxa_concordancia_ia_humano}
                      </span>
                    </div>
                  </div>

                  {/* Resumo do Pipeline */}
                  <div className="bg-slate-950/40 border border-slate-800 p-5 rounded-2xl space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                      Status da Memória em Tempo Real
                    </h3>
                    <p className="text-slate-300 text-xs leading-relaxed">
                      Cada vez que você ajusta uma aderência ou descarta um edital, o backend registra o caso como um 
                      <strong> exemplo canônico (Dynamic Few-Shot Learning)</strong>. 
                      Na próxima execução do coletor (<code className="text-cyan-300 font-mono">scraper_ai.py</code>), 
                      o Google Gemini recebe essas decisões humanas diretamente no prompt para calibrar sua classificação.
                    </p>
                  </div>
                </div>
              )}

              {/* ABA 2: EXEMPLOS POSITIVOS */}
              {abaAtiva === 'positivos' && (
                <div className="space-y-4">
                  <p className="text-xs text-slate-400">
                    Estes são os editais validados ou promovidos pela equipe que servem como padrão-ouro para o Gemini pontuar como aderente:
                  </p>
                  {(!exemplos.positivos_referencia || exemplos.positivos_referencia.length === 0) ? (
                    <div className="bg-slate-950/40 p-8 rounded-2xl border border-slate-800 text-center text-slate-500 text-xs">
                      Nenhum exemplo positivo registrado ainda. Valide ou ajuste editais nos cards para alimentar a IA!
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {exemplos.positivos_referencia.map((ex, i) => (
                        <div key={ex.id || i} className="bg-slate-950/60 border border-emerald-500/30 p-4 rounded-2xl space-y-2">
                          <div className="flex items-center justify-between gap-2">
                            <h4 className="text-sm font-bold text-white line-clamp-1">{ex.titulo}</h4>
                            <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold px-2 py-0.5 rounded-md uppercase shrink-0">
                              Aderência {ex.aderencia_final}
                            </span>
                          </div>
                          <p className="text-xs text-slate-300 font-mono bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
                            <strong>Feedback Humano:</strong> {ex.motivo_feedback || 'Classificação confirmada'}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ABA 3: FALSOS POSITIVOS DESCARTADOS */}
              {abaAtiva === 'descartados' && (
                <div className="space-y-4">
                  <p className="text-xs text-slate-400">
                    Editais que foram removidos da lista pelo usuário. A IA usa esses motivos para aprender a descartar oportunidades irrelevantes:
                  </p>
                  {descartados.length === 0 ? (
                    <div className="bg-slate-950/40 p-8 rounded-2xl border border-slate-800 text-center text-slate-500 text-xs">
                      Nenhum edital descartado. Quando você descarta um item com o botão lixeira, ele é armazenado aqui para ensinar a IA.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {descartados.map((item) => (
                        <div key={item.id} className="bg-slate-950/60 border border-rose-500/20 p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                          <div className="space-y-1.5 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="bg-rose-500/20 text-rose-300 text-[10px] font-bold px-2 py-0.5 rounded-md uppercase">
                                Descartado
                              </span>
                              <span className="text-xs text-slate-400">{item.instituicao}</span>
                            </div>
                            <h4 className="text-sm font-semibold text-slate-200 line-clamp-1">{item.titulo}</h4>
                            <p className="text-xs text-rose-300/80 bg-rose-950/20 border border-rose-800/30 p-2 rounded-lg">
                              <strong>Motivo do descarte:</strong> {item.motivo_feedback || 'Sem justificativa informada'}
                            </p>
                          </div>
                          <button
                            onClick={() => handleRestaurar(item.id)}
                            disabled={restaurandoId === item.id}
                            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-cyan-300 font-semibold px-4 py-2 rounded-xl transition-all hover:border-cyan-500/50 cursor-pointer shrink-0 self-start sm:self-center"
                          >
                            {restaurandoId === item.id ? 'Restaurando...' : 'Restaurar Edital'}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ABA 4: COMO A IA APRENDE (ARQUITETURA SENIOR) */}
              {abaAtiva === 'como_funciona' && (
                <div className="space-y-4 text-xs leading-relaxed text-slate-300">
                  <div className="bg-slate-950/60 p-5 rounded-2xl border border-slate-800 space-y-3">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <span className="text-cyan-400">⚡</span>
                      Estratégia Técnica: Active In-Context Learning (Dynamic Few-Shot)
                    </h3>
                    <p>
                      Em sistemas de triagem corporativa com LLMs, fazer o <em>Fine-Tuning</em> direto de pesos neurais é 
                      ineficiente para dados dinâmicos: é lento, caro e sofre com esquecimento catastrófico.
                    </p>
                    <p>
                      A estratégia implementada aqui utiliza o <strong>Padrão Ouro de Engenharia de IA (Human-in-the-Loop)</strong>:
                    </p>
                    <ol className="list-decimal pl-5 space-y-2 text-slate-400">
                      <li>
                        <strong className="text-slate-200">1. Âncoras Fundamentais:</strong> A IA mantém o foco institucional inegociável (Metrô, mobilidade sobre trilhos e transporte público) e a lista dinâmica de temas cadastrados.
                      </li>
                      <li>
                        <strong className="text-slate-200">2. Feedback Humano em Tempo Real:</strong> Quando um analista altera uma nota de aderência ou descarta um edital irrelevante, essa ação é persistida com status e justificativa.
                      </li>
                      <li>
                        <strong className="text-slate-200">3. Injeção de Memória no Scraper:</strong> Durante a coleta (<code className="text-cyan-400 font-mono">scraper_ai.py</code>), a IA recupera os exemplos recentes de calibração humana e os inclui no prompt.
                      </li>
                      <li>
                        <strong className="text-slate-200">4. Decisão Calibrada:</strong> A IA avalia novos editais comparando-os diretamente com os casos que a equipe já aprovou ou descartou.
                      </li>
                    </ol>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Protótipo Human-in-the-Loop Ativo
          </span>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors cursor-pointer"
          >
            Fechar
          </button>
        </div>

      </div>
    </div>
  )
}
