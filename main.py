import flet as ft
import random
import asyncio

# Motor principal assíncrono para compatibilidade total com WebAssembly/Navegadores
async def main(page: ft.Page):
    print("\n>>> MOTOR GRÁFICO WEB INICIADO <<<")
    
    page.title = "App de Recompensas"
    page.theme_mode = "dark"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    
    # --- VARIÁVEIS DE ESTADO GLOBAL ---
    saldo_usuario = 0.00
    pontos_usuario = 0
    vidas_usuario = 3  
    is_admin = False 

    # Configurações do jogo adaptadas para a nuvem
    game_state = {
        "running": False,
        "is_jumping": False,
        "velocity_y": 0.0,
        "star_bottom": 0.0,
        "obstacle_left": 0.0,
        "obstacle_speed": 8.0,
        "score_session": 0,
        "arena_width": 400
    }

    palco = ft.Column(alignment="center", horizontal_alignment="center")

    # ==========================================
    # TELA 1: MENU PRINCIPAL
    # ==========================================
    async def mostrar_tela_principal(e=None):
        game_state["running"] = False 
        page.on_keyboard_event = None 
        palco.controls.clear() 
        
        elementos = [
            ft.Text("Menu Principal", size=28, weight="bold"),
            ft.Container(height=10),
            ft.Text(f"Saldo: R$ {saldo_usuario:.2f}", size=32, weight="bold", color="green400"),
            ft.Text(f"Pontos acumulados: {pontos_usuario}", size=18, color="white60"),
            ft.Text(f"Vidas restantes: {vidas_usuario} ❤️", size=18, color="red400" if vidas_usuario == 0 else "blue400"),
            ft.Container(height=30),
            
            ft.ElevatedButton(
                "Jogar Estrela 2D 🕹️", 
                style=ft.ButtonStyle(bgcolor="green700", color="white"),
                width=250, height=50,
                on_click=mostrar_tela_jogo
            ),
            ft.Container(height=10),
            ft.OutlinedButton("Cadastrar / Sacar via Pix", icon="account_balance_wallet", width=250, on_click=mostrar_tela_pix)
        ]
        
        if is_admin:
            elementos.append(ft.Container(height=40))
            elementos.append(ft.Divider(color="white24"))
            elementos.append(ft.ElevatedButton("Intranet / Painel", icon="admin_panel_settings", bgcolor="red900", color="white"))
            
        palco.controls.extend(elementos)
        page.update() # Síncrono puro: Sem await para evitar erros de NoneType

    # ==========================================
    # TELA 2: JOGO DA ESTRELA 2D (COMPATÍVEL WEB)
    # ==========================================
    async def mostrar_tela_jogo(e=None):
        palco.controls.clear()

        # Resolução responsiva adaptável ao tamanho real da janela aberta
        largura_dispositivo = page.width if page.width else 400
        game_state["arena_width"] = min(largura_dispositivo - 35, 500)
        game_state["obstacle_left"] = game_state["arena_width"] - 30

        # Elementos móveis
        star = ft.Container(content=ft.Text("⭐", size=26), left=40, bottom=0)
        obstacle = ft.Container(content=ft.Text("🌵", size=26), left=game_state["obstacle_left"], bottom=0)
        chao = ft.Container(width=game_state["arena_width"], height=2, bgcolor="white54", bottom=0)
        
        async def realizar_pulo(event_data=None):
            if not game_state["is_jumping"] and game_state["running"]:
                game_state["is_jumping"] = True
                game_state["velocity_y"] = 13.5 

        # Camada invisível de toque/clique estendida por toda a arena
        camada_clique = ft.Container(
            bgcolor="transparent", 
            width=game_state["arena_width"], height=150, 
            on_click=realizar_pulo
        )
        
        game_stack = ft.Stack([chao, star, obstacle, camada_clique], width=game_state["arena_width"], height=150)
        
        tela_cenario = ft.Container(
            content=game_stack,
            width=game_state["arena_width"], height=150,
            bgcolor="#111111",
            border_radius=8,
            border=ft.Border.all(width=1, color="white24")
        )

        # Captura comandos de teclado de computadores
        async def detectar_teclado(keyboard_event: ft.KeyboardEvent):
            if keyboard_event.key in ["Space", "Arrow Up"]:
                await realizar_pulo()

        page.on_keyboard_event = detectar_teclado

        placar_vidas_jogo = ft.Text(f"Vidas: {vidas_usuario} ❤️", size=18, weight="bold", color="green400" if vidas_usuario > 0 else "red400")
        placar_pontos_jogo = ft.Text("Pontos: 0", size=16, weight="bold")
        text_instrucao = ft.Text("Clique abaixo para iniciar a corrida!", size=14, color="white60")

        # --- LOOP DO JOGO TOTALMENTE ASSÍNCRONO E LEVE (NÃO TRAVA O NAVEGADOR) ---
        async def game_loop():
            nonlocal vidas_usuario, pontos_usuario
            gravity = 1.2
            
            while game_state["running"]:
                # 1. Movimentação do Cacto
                game_state["obstacle_left"] -= game_state["obstacle_speed"]
                if game_state["obstacle_left"] < -20:
                    game_state["obstacle_left"] = game_state["arena_width"] - 20
                    game_state["score_session"] += 10
                    game_state["obstacle_speed"] = min(game_state["obstacle_speed"] + 0.3, 16)
                    placar_pontos_jogo.value = f"Pontos: {game_state['score_session']}"
                
                # 2. Física da Estrela
                if game_state["is_jumping"]:
                    game_state["star_bottom"] += game_state["velocity_y"]
                    game_state["velocity_y"] -= gravity
                    if game_state["star_bottom"] <= 0:
                        game_state["star_bottom"] = 0
                        game_state["is_jumping"] = False
                        game_state["velocity_y"] = 0.0
                
                # Sincronização de coordenadas gráficas
                star.bottom = game_state["star_bottom"]
                obstacle.left = game_state["obstacle_left"]
                
                # 3. Processamento de Colisões
                if (game_state["obstacle_left"] >= 25 and game_state["obstacle_left"] <= 65) and game_state["star_bottom"] <= 22:
                    game_state["running"] = False
                    break
                
                page.update() # Atualização visual instantânea
                await asyncio.sleep(0.03) # Pausa assíncrona inteligente: Devolve o controle para o navegador respirar

            # --- FLUXO GAME OVER ---
            vidas_usuario -= 1
            pontos_usuario += game_state["score_session"]
            
            botao_iniciar.text = "Jogar Novamente 🔄"
            botao_iniciar.visible = True
            
            if vidas_usuario <= 0:
                botao_iniciar.visible = False
                container_anuncio.visible = True
                text_instrucao.value = "Energia zerada! Assista ao anúncio para recarregar."
                text_instrucao.color = "amber400"
            else:
                text_instrucao.value = f"Você colidiu! Restam {vidas_usuario} energias."
                text_instrucao.color = "red400"
            
            placar_vidas_jogo.value = f"Vidas: {vidas_usuario} ❤️"
            placar_vidas_jogo.color = "red400" if vidas_usuario == 0 else "green400"
            page.update()

        async def disparar_inicio(e):
            game_state["running"] = True
            game_state["is_jumping"] = False
            game_state["star_bottom"] = 0
            game_state["obstacle_left"] = game_state["arena_width"] - 20
            game_state["obstacle_speed"] = 8.0
            game_state["score_session"] = 0
            
            botao_iniciar.visible = False
            text_instrucao.value = "Toque no cenário ou use ESPAÇO para Pular!"
            text_instrucao.color = "cyan200"
            placar_pontos_jogo.value = "Pontos: 0"
            page.update()
            
            # Executa o loop dentro do ecossistema assíncrono do próprio navegador
            asyncio.create_task(game_loop())

        async def assistir_anuncio_premiado(e):
            nonlocal vidas_usuario
            
            # LINK DO SMARTLINK DA SUA MONETAG (Substitua por um link real do seu painel)
            link_monetag = "https://SEU_SMARTLINK_AQUI.com/xxxxxx"
            
            page.snack_bar = ft.SnackBar(ft.Text("Abrindo anúncio... Não feche o jogo!"), bgcolor="blue700")
            page.snack_bar.open = True
            page.update()
            
            page.launch_url(link_monetag)
            
            text_instrucao.value = "Aguarde 15 segundos assistindo ao anúncio..."
            text_instrucao.color = "amber400"
            container_anuncio.visible = False
            page.update()
            
            # Simulação segura da contagem de tempo web
            await asyncio.sleep(15)
            
            vidas_usuario = 3
            botao_iniciar.text = "Iniciar Corrida 🚀"
            botao_iniciar.visible = True
            text_instrucao.value = "Energia restaurada com sucesso!"
            text_instrucao.color = "green400"
            placar_vidas_jogo.value = f"Vidas: {vidas_usuario} ❤️"
            placar_vidas_jogo.color = "green400"
            page.update()

        botao_iniciar = ft.ElevatedButton("Iniciar Corrida 🚀", bgcolor="green700", color="white", width=200, on_click=disparar_inicio)
        
        container_anuncio = ft.Column(
            controls=[
                ft.Text("Anúncio Patrocinado", size=11, color="white30"),
                ft.ElevatedButton("Assistir Vídeo para Recarregar 📺", icon="play_circle", bgcolor="amber700", color="black", on_click=assistir_anuncio_premiado)
            ],
            alignment="center", horizontal_alignment="center", visible=False
        )

        if vidas_usuario <= 0:
            botao_iniciar.visible = False
            container_anuncio.visible = True
            text_instrucao.value = "Sem energia! Assista ao anúncio obrigatório."
            text_instrucao.color = "amber400"

        palco.controls.extend([
            ft.Text("⭐ Corrida Estelar 2D", size=24, weight="bold"),
            ft.Container(height=5),
            ft.Row([placar_vidas_jogo, ft.Container(width=40), placar_pontos_jogo], alignment="center"),
            ft.Container(height=10),
            tela_cenario,
            ft.Container(height=15, content=text_instrucao, alignment="center"),
            botao_iniciar,
            container_anuncio,
            ft.Container(height=20),
            ft.TextButton("Voltar ao Menu Principal", on_click=mostrar_tela_principal)
        ])
        page.update()

    # ==========================================
    # TELA 3: CADASTRO PIX
    # ==========================================
    async def mostrar_tela_pix(e=None):
        game_state["running"] = False
        page.on_keyboard_event = None
        palco.controls.clear()
        
        dropdown_tipo = ft.Dropdown(
            label="Tipo de Chave", width=300,
            options=[ft.dropdown.Option("CPF"), ft.dropdown.Option("E-mail"), ft.dropdown.Option("Celular")]
        )
        campo_chave = ft.TextField(label="Digite sua chave Pix", width=300)
        
        async def salvar_pix(click):
            if not dropdown_tipo.value or not campo_chave.value:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="red700")
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Chave salva com sucesso!"), bgcolor="green700")
                await mostrar_tela_principal()
            
            page.snack_bar.open = True
            page.update()

        palco.controls.extend([
            ft.Text("Configure seus dados de recebimento", size=18, weight="bold"),
            ft.Container(height=20),
            dropdown_tipo, campo_chave,
            ft.Container(height=20),
            ft.ElevatedButton("Salvar Chave", icon="save", bgcolor="green700", color="white", on_click=salvar_pix),
            ft.Container(height=10),
            ft.TextButton("Voltar ao Menu", on_click=mostrar_tela_principal)
        ])
        page.update()

    page.controls.append(palco)
    page.update()
    await mostrar_tela_principal()

if __name__ == "__main__":
    import os
    # O Render fornece a porta de rede automaticamente nesta variável de ambiente
    porta = int(os.getenv("PORT", 8080))
    
    # Roda o Flet como um servidor web puro na porta correta
    ft.app(target=main, port=porta)