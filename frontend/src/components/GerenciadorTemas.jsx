import { useState, useEffect } from 'react'
import { API_URL } from '../config'

export default function GerenciadorTemas({ isOpen, onClose, onTemasAtualizados }) {
  const [temas, setTemas] = useState([])
  const [loading, setLoading] = useState(true)
  const [novoTema, setNovoTema] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')

  // Estado para edição inline
  const [editandoId, setEditandoId] = useState(null)
  const [editandoNome, setEditandoNome] = useState('')

  // Estado para confirmação de exclusão
  const [deletandoId, setDeletandoId] = useState(null)

  const carregarTemas = async () => {
    try {
      setLoading(true)
      setErro('')
      const res = await fetch(`${API_URL}/temas`)
      if (!res.ok) throw new Error('Falha ao obter lista de temas.')
      const data = await res.json()
      setTemas(data)
      if (onTemasAtualizados) {
        onTemasAtualizados(data)
      }
    } catch (err) {
      setErro(err.message || 'Erro ao conectar com o servidor.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      carregarTemas()
    }
  }, [isOpen])

  const handleCriarTema = async (e) => {
    e.preventDefault()
    const nomeLimpo = novoTema.trim()
    if (!nomeLimpo) {
      setErro('Digite um nome ou palavra-chave para o tema.')
      return
    }

    try {
      setSalvando(true)
      setErro('')
      setSucesso('')
      const res = await fetch(`${API_URL}/temas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: nomeLimpo })
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Erro ao criar tema.')
      }

      setNovoTema('')
      setSucesso(`Tema "${nomeLimpo}" adicionado com sucesso!`)
      await carregarTemas()
    } catch (err) {
      setErro(err.message)
    } finally {
      setSalvando(false)
    }
  }

  const handleSalvarEdicao = async (id) => {
    const nomeLimpo = editandoNome.trim()
    if (!nomeLimpo) {
      setErro('O nome do tema não pode ser vazio.')
      return
    }

    try {
      setSalvando(true)
      setErro('')
      setSucesso('')
      const res = await fetch(`${API_URL}/temas/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: nomeLimpo })
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Erro ao atualizar tema.')
      }

      setEditandoId(null)
      setEditandoNome('')
      setSucesso('Tema atualizado com sucesso!')
      await carregarTemas()
    } catch (err) {
      setErro(err.message)
    } finally {
      setSalvando(false)
    }
  }

  const handleExcluirTema = async (id, nome) => {
    try {
      setSalvando(true)
      setErro('')
      setSucesso('')
      const res = await fetch(`${API_URL}/temas/${id}`, {
        method: 'DELETE'
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Erro ao excluir tema.')
      }

      setDeletandoId(null)
      setSucesso(`Tema "${nome}" removido com sucesso!`)
      await carregarTemas()
    } catch (err) {
      setErro(err.message)
    } finally {
      setSalvando(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Cabeçalho do Modal */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.7)]"></div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Gerenciar Temas e Palavras-chave
              </h2>
              <p className="text-xs text-slate-400">
                Critérios de busca e aderência utilizados pelo coletor e pela IA
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
            title="Fechar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Mensagens de Feedback */}
        {erro && (
          <div className="mx-6 mt-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl text-xs flex items-center justify-between">
            <span>{erro}</span>
            <button onClick={() => setErro('')} className="text-rose-400 font-bold ml-2 cursor-pointer">×</button>
          </div>
        )}
        {sucesso && (
          <div className="mx-6 mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl text-xs flex items-center justify-between">
            <span>{sucesso}</span>
            <button onClick={() => setSucesso('')} className="text-emerald-400 font-bold ml-2 cursor-pointer">×</button>
          </div>
        )}

        {/* Formulário para Adicionar Novo Tema */}
        <form onSubmit={handleCriarTema} className="p-6 border-b border-slate-800 bg-slate-900/50">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Adicionar Novo Tema / Palavra-chave
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Ex: Ferrovia, VLT, Conectividade, Segurança..."
              className="flex-1 bg-slate-950 border border-slate-700 rounded-xl py-2.5 px-4 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
              value={novoTema}
              onChange={(e) => setNovoTema(e.target.value)}
              disabled={salvando}
            />
            <button
              type="submit"
              disabled={salvando || !novoTema.trim()}
              className="bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-sm transition-all shadow-md shadow-cyan-500/20 flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4" />
              </svg>
              Adicionar
            </button>
          </div>
        </form>

        {/* Lista de Temas Existentes (CRUD) */}
        <div className="p-6 overflow-y-auto flex-1 space-y-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Temas Cadastrados ({temas.length})
            </span>
            <span className="text-[11px] text-slate-500">
              Armazenados no SQLite • Editáveis em tempo real
            </span>
          </div>

          {loading ? (
            <div className="py-12 text-center text-slate-400 text-sm animate-pulse">
              Carregando temas cadastrados...
            </div>
          ) : temas.length === 0 ? (
            <div className="py-10 text-center text-slate-500 text-sm border border-slate-800 border-dashed rounded-2xl">
              Nenhum tema cadastrado. Adicione palavras-chave para o coletor!
            </div>
          ) : (
            temas.map((t) => {
              const isEditando = editandoId === t.id
              const isDeletando = deletandoId === t.id

              return (
                <div
                  key={t.id}
                  className="group flex items-center justify-between p-3.5 bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-2xl transition-all"
                >
                  {isEditando ? (
                    <div className="flex items-center gap-2 flex-1 mr-2">
                      <input
                        type="text"
                        className="flex-1 bg-slate-900 border border-cyan-500 rounded-lg py-1.5 px-3 text-sm text-white focus:outline-none"
                        value={editandoNome}
                        onChange={(e) => setEditandoNome(e.target.value)}
                        autoFocus
                      />
                      <button
                        type="button"
                        onClick={() => handleSalvarEdicao(t.id)}
                        disabled={salvando}
                        className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 p-1.5 rounded-lg transition-colors cursor-pointer"
                        title="Salvar"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={() => { setEditandoId(null); setEditandoNome('') }}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-400 p-1.5 rounded-lg transition-colors cursor-pointer"
                        title="Cancelar"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3 flex-1 min-w-0 pr-3">
                      <span className="w-2 h-2 rounded-full bg-cyan-500/70"></span>
                      <span className="text-sm font-medium text-slate-200 truncate" title={t.nome}>
                        {t.nome}
                      </span>
                    </div>
                  )}

                  {!isEditando && (
                    <div className="flex items-center gap-2">
                      {isDeletando ? (
                        <div className="flex items-center gap-1.5 bg-rose-950/40 border border-rose-500/40 p-1 rounded-xl">
                          <span className="text-[11px] text-rose-300 font-semibold px-2">Excluir?</span>
                          <button
                            type="button"
                            onClick={() => handleExcluirTema(t.id, t.nome)}
                            disabled={salvando}
                            className="bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
                          >
                            Sim
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeletandoId(null)}
                            className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-2 py-1 rounded-lg transition-colors cursor-pointer"
                          >
                            Não
                          </button>
                        </div>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => {
                              setEditandoId(t.id)
                              setEditandoNome(t.nome)
                              setDeletandoId(null)
                            }}
                            className="text-slate-400 hover:text-cyan-400 p-2 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
                            title="Editar tema"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setDeletandoId(t.id)
                              setEditandoId(null)
                            }}
                            className="text-slate-400 hover:text-rose-400 p-2 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
                            title="Excluir tema"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>

        {/* Rodapé do Modal */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/90 flex justify-between items-center text-xs text-slate-500">
          <span>O coletor considerará todos os temas ativos para raspagem e medição semântica.</span>
          <button
            onClick={onClose}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-4 py-2 rounded-xl transition-colors cursor-pointer"
          >
            Fechar
          </button>
        </div>

      </div>
    </div>
  )
}
