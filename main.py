import flet as ft
import threading
import time
import os
import requests

# Versão atual do aplicativo para o sistema de atualização remota
APP_VERSION = "1.0.0" 
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/seu-usuario/seu-repositorio/main/version.json"

def main(page: ft.Page):
    page.title = "StarRun Premium"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 12

    palco = ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
    page.add(palco)

    # --- ELEMENTOS DE ÁUDIO ---
    snd_bg = ft.Audio(src="https://actions.google.com/sounds/v1/science_fiction/ambient_space_drive.ogg", autoplay=False, volume=0.2, release_mode="loop")
    snd_jump = ft.Audio(src="https://actions.google.com/sounds/v1/cartoon/slide_whistle_up.ogg", autoplay=False, volume=0.4)
    snd_point = ft.Audio(src="https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg", autoplay=False, volume=0.4)
    snd_over = ft.Audio(src="https://actions.google.com/sounds/v1/science_fiction/space_emergency.ogg", autoplay=False, volume=0.5)
    page.overlay.extend([snd_bg, snd_jump, snd_point, snd_over])

    # --- ESTADO DO JOGO ---
    state = {
        "saldo": 0.00, "pontos": 0, "vidas": 3, "anuncios_assistidos": 0,
        "skin_atual": "⭐", "cenario_atual": "Espaço Oblívio",
        "skins_desbloqueadas": ["⭐"], "cenarios_comprados": ["Espaço Oblívio"],
        "running": False, "is_jumping": False, "velocity_y": 0.0,
        "star_bottom": 0, "obstacle_left": 310, "obstacle_speed": 12.0,
        "score_session": 0, "fase_atual": 1, "tela_cheia": False,
        "temas_desbloqueados": ["Padrão Cyber"], "tema_custom_atual": "Padrão Cyber"
    }

    cores_cenarios = {"Espaço Oblívio": "#111111", "Deserto Escaldante": "#3a2212", "Cyberpunk Neon": "#1a0033"}
    estilos_temas = {
        "Padrão Cyber": {"bg": "#111111", "card": "#1e1e1e", "texto": "amber400"},
        "Vulcão Ultravioleta": {"bg": "#230026", "card": "#3d0042", "texto": "pink300"},
        "Oceano Profundo": {"bg": "#021124", "card": "#052247", "texto": "cyan400"}
    }

    # --- ARMAZENAMENTO LOCAL SEGURO (NATIVO NO ANDROID) ---
    def carregar_sessao_salva():
        try:
            # Proteção caso o storage demore a responder no primeiro handshake
            if not page.client_storage: return
            s = page.client_storage.get("starrun_saldo")
            if s is not None: state["saldo"] = float(s)
            p = page.client_storage.get("starrun_pontos")
            if p is not None: state["pontos"] = int(p)
            a = page.client_storage.get("starrun_ads")
            if a is not None: state["anuncios_assistidos"] = int(a)
            sk = page.client_storage.get("starrun_skin")
            if sk is not None: state["skin_atual"] = sk
            ce = page.client_storage.get("starrun_cenario")
            if ce is not None: state["cenario_atual"] = ce
        except Exception:
            pass

    def salvar_progresso_local():
        try:
            if not page.client_storage: return
            page.client_storage.set("starrun_saldo", str(state["saldo"]))
            page.client_storage.set("starrun_pontos", str(state["pontos"]))
            page.client_storage.set("starrun_ads", str(state["anuncios_assistidos"]))
            page.client_storage.set("starrun_skin", state["skin_atual"])
            page.client_storage.set("starrun_cenario", state["cenario_atual"])
        except Exception:
            pass

    # --- VERIFICADOR DE ATUALIZAÇÕES REMOTAS (GITHUB) ---
    def verificar_atualizacao():
        def buscar_dados():
            try:
                response = requests.get(GITHUB_VERSION_URL, timeout=5)
                if response.status_code == 200:
                    dados = response.json()
                    if dados.get("latest_version") != APP_VERSION:
                        def fechar_banner(e): page.banner.open = False; page.update()
                        def ir_para_download(e): page.launch_url(dados.get("download_url"))
                        
                        page.banner = ft.Banner(
                            bgcolor=ft.colors.AMBER_900,
                            leading=ft.Icon(ft.icons.UPDATE, color=ft.colors.WHITE),
                            content=ft.Text(f"Nova versão disponível ({dados.get('latest_version')})! Atualize para continuar ganhando."),
                            actions=[
                                ft.TextButton("Baixar APK", on_click=ir_para_download),
                                ft.TextButton("Depois", on_click=fechar_banner),
                            ],
                        )
                        page.banner.open = True
                        page.update()
            except Exception:
                pass
        threading.Thread(target=buscar_dados, daemon=True).start()

    # --- INTERFACE DE CONFIGURAÇÕES ---
    def abrir_configuracoes(e):
        def alterar_tema_base(e):
            page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
            page.update()

        def comprar_tema_ad(nome_tema):
            def acao(e):
                if nome_tema in state["temas_desbloqueados"]:
                    state["tema_custom_atual"] = nome_tema
                else:
                    # Sistema de monetização por anúncio premiado
                    page.launch_url("https://omg10.com/4/11105173")
                    state["anuncios_assistidos"] += 1
                    state["temas_desbloqueados"].append(nome_tema)
                    state["tema_custom_atual"] = nome_tema
                    salvar_progresso_local()
                dialogo_config.open = False
                mostrar_tela_principal()
            return acao

        opcoes = ft.Column([
            ft.ElevatedButton("Modo Claro/Escuro ☀️🌙", on_click=alterar_tema_base, width=260),
            ft.Divider(),
            ft.Text("Temas por Vídeo Premiado:", size=12, color="white60")
        ])
        
        for t in estilos_temas.keys():
            ja_tem = t in state["temas_desbloqueados"]
            label = f"Usar {t}" if ja_tem else f"🔓 Desbloquear {t} (1 Ad)"
            opcoes.controls.append(ft.ElevatedButton(label, on_click=comprar_tema_ad(t), width=260, bgcolor="purple700" if not ja_tem else "blue700"))

        dialogo_config.content = opcoes
        dialogo_config.open = True
        page.update()

    dialogo_config = ft.AlertDialog(title=ft.Text("Configurações"), actions=[ft.TextButton("Fechar", on_click=lambda e: setattr(dialogo_config, "open", False) or page.update())])
    page.overlay.append(dialogo_config)

    def obter_cabecalho():
        tema = estilos_temas.get(state["tema_custom_atual"], estilos_temas["Padrão Cyber"])
        return ft.Row([
            ft.Text("StarRun Premium", size=20, weight="bold", color=tema["texto"]),
            ft.IconButton(ft.icons.SETTINGS, icon_color=tema["texto"], on_click=abrir_configuracoes)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=330)

    # ==========================================
    # TELAS COMPORTAMENTAIS (MENU E JOGO)
    # ==========================================
    def mostrar_tela_principal(e=None):
        state["running"] = False
        palco.controls.clear()
        tema = estilos_temas.get(state["tema_custom_atual"], estilos_temas["Padrão Cyber"])
        page.bgcolor = tema["bg"]

        palco.controls.extend([
            obter_cabecalho(),
            ft.Card(
                color=tema["card"],
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Saldo Disponível", size=12, color="white60"),
                        ft.Text(f"R$ {state['saldo']:.2f}", size=32, weight="bold", color="green400"),
                        ft.Text(f"{state['pontos']} pontos acumulados", size=12, color="white40")
                    ], horizontal_alignment="center"), padding=15
                ), width=330
            ),
            ft.ElevatedButton("Jogar Corrida Estelar 🕹️", bgcolor="green700", color="white", width=260, height=45, on_click=mostrar_tela_jogo),
            ft.ElevatedButton("Sacar via Pix 💰", bgcolor="teal700", color="white", width=260, height=45, on_click=mostrar_tela_pix)
        ])
        page.update()

    def mostrar_tela_jogo(e=None):
        palco.controls.clear()
        largura_arena = 440 if state["tela_cheia"] else 330
        altura_arena = 140
        state["obstacle_left"] = largura_arena - 30

        star = ft.Container(content=ft.Text(state["skin_atual"], size=24), left=40, bottom=0, animate=ft.animation.Animation(80, "linear"))
        obstacle = ft.Container(content=ft.Text("🌵", size=24), left=state["obstacle_left"], bottom=0, animate=ft.animation.Animation(80, "linear"))
        chao = ft.Container(width=largura_arena, height=2, bgcolor="white54", bottom=0)
        game_stack = ft.Stack([chao, star, obstacle], width=largura_arena, height=altura_arena)

        def saltar(e):
            if not state["is_jumping"] and state["running"]:
                state["is_jumping"] = True
                state["velocity_y"] = 15.0
                try: snd_jump.play()
                except: pass

        conteudo_jogo = ft.Container(content=game_stack, width=largura_arena, height=altura_arena, bgcolor="#111111", border_radius=10, on_click=saltar)
        placar = ft.Text("Pontos: 0", size=14, weight="bold")

        def game_loop():
            gravity = 1.8
            while state["running"]:
                state["obstacle_left"] -= state["obstacle_speed"]
                if state["obstacle_left"] < -20:
                    state["obstacle_left"] = largura_arena - 30
                    state["score_session"] += 10
                    placar.value = f"Pontos: {state['score_session']}"
                    try: snd_point.play()
                    except: pass

                if state["is_jumping"]:
                    state["star_bottom"] += int(state["velocity_y"])
                    state["velocity_y"] -= gravity
                    if state["star_bottom"] <= 0:
                        state["star_bottom"] = 0
                        state["is_jumping"] = False

                star.bottom = state["star_bottom"]
                obstacle.left = state["obstacle_left"]

                if (20 <= state["obstacle_left"] <= 60) and state["star_bottom"] <= 20:
                    state["running"] = False
                    try: snd_over.play()
                    except: pass
                    break

                conteudo_jogo.update()
                placar.update()
                time.sleep(0.08)

            state["vidas"] -= 1
            state["pontos"] += state["score_session"]
            state["saldo"] = state["pontos"] * 0.001
            salvar_progresso_local()
            mostrar_tela_principal()

        def iniciar_partida(e):
            state["running"] = True
            btn_start.visible = False
            page.update()
            threading.Thread(target=game_loop, daemon=True).start()

        btn_start = ft.ElevatedButton("Dar Start 🚀", on_click=iniciar_partida, bgcolor="green700", color="white")
        
        palco.controls.extend([
            obber_hdr := obter_cabecalho(),
            ft.Row([ft.Text("Arena Ativa", weight="bold"), placar], alignment="space_between", width=largura_arena),
            conteudo_jogo,
            btn_start,
            ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)
        ])
        page.update()

    def mostrar_tela_pix(e=None):
        palco.controls.clear()
        campo_chave = ft.TextField(label="Chave Pix", width=300)
        campo_valor = ft.TextField(label="Valor (R$)", width=300, value=f"{state['saldo']:.2f}")

        def processar_saque(e):
            v = float(campo_valor.value.replace(",", "."))
            if v > state["saldo"] or v < 10.0:
                page.snack_bar = ft.SnackBar(ft.Text("Mínimo R$ 10,00 ou saldo insuficiente."), bgcolor="red700")
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Saque solicitado com sucesso!"), bgcolor="green700")
                state["saldo"] -= v
                state["pontos"] = int(state["saldo"] / 0.001)
                salvar_progresso_local()
                mostrar_tela_principal()
            page.snack_bar.open = True
            page.update()

        palco.controls.extend([
            obter_cabecalho(),
            ft.Text("Resgate Pix 💰", size=20, weight="bold"),
            campo_chave, campo_valor,
            ft.ElevatedButton("Confirmar Saque", on_click=processar_saque, bgcolor="teal700", color="white", width=300),
            ft.TextButton("Voltar", on_click=mostrar_tela_principal)
        ])
        page.update()

    carregar_sessao_salva()
    mostrar_tela_principal()
    verificar_atualizacao()

if __name__ == "__main__":
    ft.app(target=main, port=int(os.getenv("PORT", 8080)))