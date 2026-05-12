import pygame, random, math, sys, json, os, time

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Línea 55 Tycoon v15.0 - Eventos y La Matanza Edition")
CLOCK = pygame.time.Clock()

C_BG_DIA, C_BG_NOCHE = (10, 16, 26), (5, 8, 15)
C_UI_DIA, C_UI_NOCHE = (28, 36, 52), (20, 25, 38)
C_ACCENT, C_GREEN, C_RED, C_GOLD = (0, 210, 255), (65, 235, 125), (255, 75, 75), (255, 215, 0)
C_YELLOW, C_PURPLE, C_ORANGE = (255, 240, 100), (190, 130, 255), (255, 160, 0)
C_WHITE, C_GRAY, C_DARK = (250, 250, 250), (95, 100, 115), (16, 20, 32)
C_MSG_BG, C_CHOFER_MSG = (22, 28, 40), (35, 25, 15)

FONT_S = pygame.font.SysFont("arial", 22, bold=True)
FONT_MS = pygame.font.SysFont("arial", 20, bold=True)
FONT_M = pygame.font.SysFont("arial", 34, bold=True)
FONT_L = pygame.font.SysFont("arial", 48, bold=True)
FONT_XL = pygame.font.SysFont("arial", 64, bold=True)

def make_beep(freq=800, dur=0.1):
    arr = bytearray()
    for i in range(int(22050 * dur)):
        val = int(32767 * math.sin(2 * math.pi * freq * i / 22050))
        arr.extend(val.to_bytes(2, byteorder='little', signed=True))
        arr.extend(val.to_bytes(2, byteorder='little', signed=True))
    return pygame.mixer.Sound(buffer=bytes(arr))

SND_COBRO = make_beep(1200, 0.08)
SND_HIRE = make_beep(600, 0.1)
SND_ALERT = make_beep(300, 0.3)
SND_CLICK = make_beep(1000, 0.05)
SND_BREAK = make_beep(200, 0.4)
SND_QUIT = make_beep(400, 0.2)
SND_MSG = make_beep(800, 0.06)
SND_PUERTA = make_beep(250, 0.15)
SND_EVENT = make_beep(500, 0.2)

RUTAS = {
    "A": {
        "nombre": "S. Justo - Belgrano",
        "stops": ["San Justo (Term)", "UNLaM", "Shopping", "Policlínico", "Don Bosco", "Liniers",
                  "Gral Paz", "Estadio Vélez", "Villa Luro", "Plaza Flores", "Caballito",
                  "Pque Centenario", "Villa Crespo", "Palermo Soho", "Plaza Italia", "Belgrano (Term)"],
        "desbloqueada": True,
        "costo": 0
    },
    "B": {
        "nombre": "S. Justo - Retiro",
        "stops": ["San Justo (Term)", "Ramos Mejía", "Haedo", "Morón", "Castelar", "Ituzaingó",
                  "Padua", "Merlo", "Liniers", "Floresta", "Flores", "Caballito", "Almagro", "Retiro"],
        "desbloqueada": False,
        "costo": 500000
    },
    "C": {
        "nombre": "S. Justo - Const.",
        "stops": ["San Justo (Term)", "Villa Madero", "Villa Celina", "Villa Lugano", "Lugano",
                  "Soldati", "Pompeya", "Barracas", "Constitución"],
        "desbloqueada": False,
        "costo": 800000
    }
}

FRASES_CHOFER = [
    "Paga rata!", "Che, corranse para atrás!", "No me toquen el bondi!", "Dale chofer, no duermas!",
    "Suban de a uno, manga de locos!", "Aguante la 55 papá!", "Che, frená que me caigo!",
    "No seas rata, pagá el boleto!", "Vamo arriba que hay pica!", "Se rompió todo, mal ahí."
]

FRASES_TERMINAL = [
    "Terminal San Justo operativa.",
    "Próximo bondi en 5 min.",
    "Ruta libre, dale!"
]

class Chofer:
    def __init__(self, nombre, personalidad, sueldo, cansancio=0.0, contratado=False, moral=85):
        self.nombre = nombre
        self.personalidad = personalidad
        self.sueldo = sueldo
        self.cansancio = cansancio
        self.moral = moral
        self.unidad = None
        self.contratado = contratado

    def to_dict(self):
        return {"n": self.nombre, "p": self.personalidad, "s": self.sueldo,
                "c": self.cansancio, "m": self.moral, "con": self.contratado}

class Unidad:
    def __init__(self, id_u, motor=1, frenos=1):
        self.id = id_u
        self.motor_lvl = motor
        self.frenos_lvl = frenos
        self.pasajeros = 0
        self.capacidad = 70
        self.pos_idx = -1
        self.progreso = 0.0
        self.chofer = None
        self.oscilar = 0.0
        self.averiado = 0.0
        self.viajes_sin_service = 0
        self.ruta_key = "A"

    def reset(self):
        if self.chofer: self.chofer.unidad = None
        self.pasajeros = 0
        self.pos_idx = -1
        self.progreso = 0.0
        self.chofer = None
        self.averiado = 0.0

    def to_dict(self):
        return {"id": self.id, "m": self.motor_lvl, "f": self.frenos_lvl,
                "pax": self.pasajeros, "idx": self.pos_idx, "prog": self.progreso,
                "viajes": self.viajes_sin_service, "ruta": self.ruta_key}

class Juego:
    def __init__(self):
        self.estado = "MENU"
        self.tutorial_msgs = [
            "¡Bienvenido a la 55, el orgullo de La Matanza!",
            "Despachá bondis con SALIR y cobrá subsidios.",
            "En STAFF podés contratar y RAJAR choferes.",
            "Mejorá frenos en el TALLER o te quedás a gamba.",
            "Atento a los EVENTOS, tus decisiones importan."
        ]

        self.cargar_datos_eventos()
        self.reiniciar_todo()
        self.cargar_partida()

        self.btn_mapa = pygame.Rect(10, 1180, 135, 80)
        self.btn_staff = pygame.Rect(150, 1180, 135, 80)
        self.btn_taller = pygame.Rect(290, 1180, 135, 80)
        self.btn_despachar = pygame.Rect(430, 1180, 135, 80)
        self.btn_cobrar = pygame.Rect(570, 1180, 135, 80)
        self.btn_pausa_rect = pygame.Rect(WIDTH-70, 15, 60, 55)

        self.rect_terminal_msg = pygame.Rect(WIDTH-220, 78, 200, 42)
        self.rect_chofer_msg = pygame.Rect(10, 1075, WIDTH-20, 95)
        self.rect_reloj = pygame.Rect(WIDTH-220, 15, 140, 55)
        
        self.btns_hire = []
        self.btns_fire = []
        self.btns_upg = []
        self.btns_menu = []
        self.btn_rutas = []
        self.btns_evento_opciones = []
        
        self.btn_confirm = None
        self.btn_cancel = None
        self.btn_volver_logros = None
        self.btn_reset_opc = None
        self.btn_volver_opc = None
        
        self.popup_type = None
        self.tooltip_data = None
        self.tooltip_timer = 0

        if not hasattr(self, "logros"):
            self.logros = {
                "primer_viaje": False,
                "millonario": False,
                "flota_full": False,
                "sin_accidentes": False,
                "moral_100": False
            }
        if not hasattr(self, "stats"):
            self.stats = {
                "recaudado_total": 0,
                "pasajeros_transportados": 0,
                "viajes_completados": 0,
                "accidentes": 0,
                "gastado_mantenimiento": 0
            }

    def cargar_datos_eventos(self):
        self.eventos_db = [
            {
                "id": 0, "titulo": "VENDEDOR AMBULANTE",
                "txt": ["Un pibe se sube en Liniers con", "una bolsa de medias 'originales'."],
                "opciones": ["Dejalo, algo vende", "Rajalo ya", "Comprale 2 pares"]
            },
            {
                "id": 1, "titulo": "PASAJERA ENOJADA",
                "txt": ["Una señora se sube y le pega una", "puteada a todo el bondi por la demora."],
                "opciones": ["Dejala que se desahogue", "Bajala de una", "Dale paso y asiento"]
            },
            {
                "id": 2, "titulo": "SINDICATO PESADO",
                "txt": ["Te cae un flaco de chaleco:", "'Por 50 lucas te cuidamos la línea, socio'."],
                "opciones": ["Pagar (Inmunidad)", "No gracias", "Negociar"]
            },
            {
                "id": 3, "titulo": "PARITARIAS UTA",
                "txt": ["Los choferes piden un aumento", "urgente o paran 24hs."],
                "opciones": ["Aceptar aumento", "Negociar un 5%", "No hay plata"]
            },
            {
                "id": 4, "titulo": "CONTROL SORPRESA",
                "txt": ["Sube un inspector. Hay 3", "pasajeros sin pagar el boleto."],
                "opciones": ["Hacerte el boludo", "Bajarlos", "Pagarles vos"]
            },
            {
                "id": 5, "titulo": "EL SANGUCHITO",
                "txt": ["En Caballito el bondi frena 2 min", "porque todos bajan por un choripán."],
                "opciones": ["Bocinar y seguir", "Esperar 30s", "Bajarte a comprar"]
            },
            {
                "id": 6, "titulo": "CORTE TOTAL",
                "txt": ["Piquete pesado en Gral Paz.", "Alternativas cortadas y quemando gomas."],
                "opciones": ["Desviar por colectora", "Esperar que se abra", "Sobornar a los pibes"]
            },
            {
                "id": 7, "titulo": "DILUVIO UNIVERSAL",
                "txt": ["Empieza a llover fuerte y se llueve", "todo adentro de un bondi."],
                "opciones": ["Mandar al taller", "Poner balde y seguir", "Ignorar las quejas"]
            },
            {
                "id": 8, "titulo": "LA BARRA BRAVA",
                "txt": ["Banda gigante de hinchas sube", "en pedo y cantando."],
                "opciones": ["Dejarlos subir a todos", "Limitar a 10", "Cancelar el viaje"]
            },
            {
                "id": 9, "titulo": "BILLETE GRANDE",
                "txt": ["Un pasajero te da un billete de 1000", "y te exige cambio exacto."],
                "opciones": ["Decirle que no tenés", "Hacer vaquita", "Cargarle la SUBE"]
            }
        ]

    def reiniciar_todo(self):
        self.dinero = 600000
        self.subsidio_pendiente = 0
        self.tutorial_idx = 0
        self.hora = 4.0
        self.ruta_actual = "A"
        self.unidades = [Unidad(i) for i in range(1, 13)]
        self.staff = [Chofer("Cacho", "Pro", 1500, contratado=True)]
        self.bolsa = self.generar_bolsa()
        self.actualizar_recorrido()
        self.vista = "MAPA"
        self.scroll_y = 0
        self.game_over = False
        self.pausa = False
        self.frase_terminal = FRASES_TERMINAL[0]
        self.inmunidad_piquete_hasta = 0
        
        self.timer_radio = 0
        self.timer_evento_ambiente = time.time()
        self.timer_proximo_evento_popup = time.time() + random.uniform(30, 60)
        self.evento_popup_actual = None
        
        self.timer_autosave = time.time()
        self.notificaciones = []
        self.mensajes_chofer = []
        self.timer_frase_chofer = 0
        self.popups_viaje = []
        self.stats = {
            "recaudado_total": 0,
            "pasajeros_transportados": 0,
            "viajes_completados": 0,
            "accidentes": 0,
            "gastado_mantenimiento": 0
        }

    def actualizar_recorrido(self):
        ruta = RUTAS[self.ruta_actual]
        self.recorrido = [{"n": n, "dem": random.randint(15, 40), "corte": False} for n in ruta["stops"]]

    def generar_bolsa(self):
        nombres = ["El Tarta", "Beto", "Pocho", "El Rengo", "Franco", "Cloe", "Luffy", "Cholo"]
        per = ["Agresivo", "Tranquilo", "Vago", "Pro"]
        bolsa = []
        for _ in range(8):
            moral = random.randint(40, 90)
            if moral >= 40:
                bolsa.append(Chofer(f"{random.choice(nombres)}", random.choice(per), random.randint(2200, 4800), moral=moral))
        return bolsa

    def modificar_moral_todos(self, cant):
        for c in self.staff:
            c.moral = max(0, min(100, c.moral + cant))
            
    def modificar_demanda_global(self, cant):
        for p in self.recorrido:
            p["dem"] = max(0, min(100, p["dem"] + cant))
            
    def modificar_pasajeros_todos(self, cant):
        for u in self.unidades:
            if u.pos_idx != -1:
                u.pasajeros = max(0, min(u.capacidad, u.pasajeros + cant))

    def bondi_random_activo(self):
        activos = [u for u in self.unidades if u.pos_idx != -1]
        return random.choice(activos) if activos else None

    def aplicar_efecto_evento(self, id_evento, idx_opcion):
        if id_evento == 0:
            if idx_opcion == 0: self.dinero += 2000; self.modificar_moral_todos(-5); self.add_notif("Dejaste al fisura. +$2000 pero bajó la moral.")
            elif idx_opcion == 1: self.modificar_moral_todos(10); self.modificar_pasajeros_todos(-1); self.add_notif("Rajaste al pibe al toque. Choferes contentos.")
            elif idx_opcion == 2: self.dinero -= 500; self.modificar_moral_todos(5); self.add_notif("Le compraste medias de onda. -$500")
        elif id_evento == 1:
            if idx_opcion == 0: self.modificar_demanda_global(10); self.modificar_moral_todos(-5); self.add_notif("La abuela puteó de lo lindo.")
            elif idx_opcion == 1: self.modificar_demanda_global(-20); self.modificar_moral_todos(10); self.add_notif("Bajaste a la abuela enojada.")
            elif idx_opcion == 2: self.dinero -= 300; self.modificar_moral_todos(15); self.add_notif("Asiento y pase gratis. Sos un crack.")
        elif id_evento == 2:
            if idx_opcion == 0: self.dinero -= 50000; self.inmunidad_piquete_hasta = time.time() + 600; self.add_notif("Arreglaste con el sindicato. Sin piquetes un rato.")
            elif idx_opcion == 1: 
                self.modificar_moral_todos(20)
                if self.recorrido: random.choice(self.recorrido)["corte"] = True
                self.add_notif("Te plantaste, pero te clavaron un piquete!")
            elif idx_opcion == 2: 
                self.dinero -= 20000
                if random.random() < 0.5 and self.recorrido: random.choice(self.recorrido)["corte"] = True
                self.add_notif("Negociaste, pero puede fallar...")
        elif id_evento == 3:
            if idx_opcion == 0: self.dinero -= 15000; self.modificar_moral_todos(20); self.add_notif("Aceptaste paritarias al toque. -$15k")
            elif idx_opcion == 1: 
                if random.random() < 0.5: self.modificar_moral_todos(-20); self.add_notif("Se pudrió todo en la negociación.")
                else: self.modificar_moral_todos(5); self.add_notif("Acordaste un 5% transitorio.")
            elif idx_opcion == 2: 
                self.modificar_moral_todos(-30)
                if random.random() < 0.25 and self.staff: 
                    random.choice(self.staff).moral = 0
                    self.add_notif("No hay plata y casi te renuncia uno!")
                else: self.add_notif("No hay plata. Clima re tenso.")
        elif id_evento == 4:
            if idx_opcion == 0:
                if random.random() < 0.7: self.dinero -= 15000; self.add_notif("Te escrachó el inspector! Multa -$15k")
                else: self.add_notif("Zafaste del control de milagro.")
            elif idx_opcion == 1: self.modificar_moral_todos(10); self.modificar_pasajeros_todos(-3); self.add_notif("Hiciste bajar a los colados.")
            elif idx_opcion == 2: self.dinero -= 1800; self.modificar_moral_todos(15); self.modificar_demanda_global(5); self.add_notif("Pagaste los boletos de tu bolsillo.")
        elif id_evento == 5:
            if idx_opcion == 0: self.modificar_demanda_global(-5); self.add_notif("Bocinazo. La gente murmura.")
            elif idx_opcion == 1: self.modificar_demanda_global(5); self.modificar_moral_todos(5); self.add_notif("Esperaste. Alto chori pegaron.")
            elif idx_opcion == 2: self.dinero -= 800; self.modificar_moral_todos(10); self.add_notif("Compraste chori para la tropa.")
        elif id_evento == 6:
            if idx_opcion == 0: self.modificar_pasajeros_todos(-5); self.add_notif("Desviaste y se bajó un par enojados.")
            elif idx_opcion == 1: self.modificar_moral_todos(-5); self.add_notif("Toca esperar. La demora pega mal.")
            elif idx_opcion == 2: self.dinero -= 10000; self.add_notif("Pagaste el peaje blue. -$10k")
        elif id_evento == 7:
            if idx_opcion == 0: self.dinero -= 20000; self.add_notif("Mapeaste el techo. -$20k en Taller.")
            elif idx_opcion == 1: 
                self.modificar_pasajeros_todos(-10)
                u = self.bondi_random_activo()
                if u: u.averiado = 5.0
                self.add_notif("Pusiste balde, pero se te rompió otra cosa!")
            elif idx_opcion == 2: self.modificar_moral_todos(-15); self.add_notif("Ignoraste todo. Chofer empapado y re caliente.")
        elif id_evento == 8:
            if idx_opcion == 0: self.modificar_pasajeros_todos(50); self.modificar_moral_todos(-10); self.dinero += 30000; self.add_notif("¡Copa Libertadores en la 55! +$30k")
            elif idx_opcion == 1: self.modificar_pasajeros_todos(10); self.add_notif("Subieron pocos, safaste del bardo.")
            elif idx_opcion == 2: self.modificar_moral_todos(-20); self.modificar_pasajeros_todos(-100); self.add_notif("Viaje cancelado. Todos a la calle.")
        elif id_evento == 9:
            if idx_opcion == 0: self.modificar_demanda_global(-5); self.add_notif("Sin cambio, se bajó puteando.")
            elif idx_opcion == 1: self.modificar_moral_todos(5); self.add_notif("Vaquita solidaria de los pasajeros.")
            elif idx_opcion == 2: 
                if random.random() < 0.5: self.modificar_moral_todos(5); self.add_notif("Le cargaste la SUBE, quedó chocho.")
                else: self.modificar_moral_todos(-5); self.add_notif("Le cargaste mal, se enojó igual.")

    def simular(self, dt):
        if self.estado != "JUEGO": return
        if self.evento_popup_actual: return # Congela todo si hay evento
        if self.pausa or self.game_over or self.tutorial_idx < len(self.tutorial_msgs): return

        self.hora = (self.hora + dt * 0.05) % 24

        # Disparador de eventos aleatorios interactivos
        if time.time() > self.timer_proximo_evento_popup:
            self.timer_proximo_evento_popup = time.time() + random.uniform(30, 60)
            if random.random() < 0.15:
                self.evento_popup_actual = random.choice(self.eventos_db)
                SND_EVENT.play()
                return

        if time.time() - self.timer_autosave > 30:
            self.guardar_partida()
            self.timer_autosave = time.time()

        es_noche = 22 <= self.hora or self.hora < 6
        mult_pico = 3.0 if (7 <= self.hora <= 9) or (17 <= self.hora <= 19) else 1.0
        if es_noche: mult_pico *= 0.6
        
        for p in self.recorrido:
            p["dem"] = min(100, p["dem"] + (0.05 * mult_pico))

        self.timer_frase_chofer -= dt
        if self.timer_frase_chofer <= 0 and self.staff:
            chofer_random = random.choice(self.staff)
            frase = random.choice(FRASES_CHOFER)
            self.mensajes_chofer.append({"m": f"{chofer_random.nombre}: {frase}", "t": time.time()})
            SND_MSG.play()
            self.timer_frase_chofer = random.uniform(6, 10)
            if len(self.mensajes_chofer) > 5:
                self.mensajes_chofer.pop(0)

        for u in self.unidades:
            if u.pos_idx != -1:
                if not u.chofer:
                    u.reset()
                    continue

                if u.averiado > 0:
                    u.averiado -= dt
                    continue
                
                frenos_safe = max(1, u.frenos_lvl)
                chance_rotura = 0.0006 * (6 - u.frenos_lvl)
                if random.random() < chance_rotura:
                    u.averiado = 6.0
                    self.add_notif(f"Int {u.id}: ¡Humo en los frenos!")
                    self.stats["accidentes"] += 1
                    SND_BREAK.play()
                    continue

                vel = (0.0055 + (u.motor_lvl * 0.002))
                if u.chofer.personalidad == "Agresivo": vel *= 1.35
                if u.chofer.cansancio > 70: vel *= 0.85
                if self.recorrido[u.pos_idx]["corte"]: vel *= 0.1

                u.progreso += vel * dt * 60
                u.oscilar += 0.5
                u.chofer.cansancio += (0.028 / frenos_safe) * dt * 60

                if u.chofer.moral <= 0:
                    self.add_notif(f"{u.chofer.nombre} se fue a la mierda. Moral 0.")
                    SND_QUIT.play()
                    self.abandonar_ruta(u)
                    continue
                
                if u.progreso >= 1.0:
                    u.progreso = 0
                    u.pos_idx += 1
                    if u.pos_idx < len(self.recorrido):
                        self.parada_bus(u)
                    else:
                        self.finalizar_viaje(u)

        if time.time() - self.timer_evento_ambiente > 18:
            self.lanzar_evento_ambiente()
            self.timer_evento_ambiente = time.time()

        self.notificaciones = [n for n in self.notificaciones if time.time() - n['t'] < 5]
        self.mensajes_chofer = [n for n in self.mensajes_chofer if time.time() - n['t'] < 4]
        self.popups_viaje = [p for p in self.popups_viaje if time.time() - p['t'] < 2]
        self.chequear_logros()

        if self.dinero < -200000:
            self.game_over = True
            SND_ALERT.play()
            
        if self.tooltip_timer > 0:
            self.tooltip_timer -= dt
            if self.tooltip_timer <= 0:
                self.tooltip_data = None

    def chequear_logros(self):
        if not self.logros["primer_viaje"] and any(u.pos_idx >= 0 for u in self.unidades):
            self.logros["primer_viaje"] = True
            self.add_notif("LOGRO: Primer viaje! Aguante la 55.")
        if not self.logros["millonario"] and self.dinero > 1000000:
            self.logros["millonario"] = True
            self.add_notif("LOGRO: Millonario! Te forraste.")
        if not self.logros["flota_full"] and all(u.motor_lvl >= 5 for u in self.unidades[:8]):
            self.logros["flota_full"] = True
            self.add_notif("LOGRO: Flota Full! Son máquinas.")
        if not self.logros["sin_accidentes"] and self.stats["accidentes"] == 0 and self.stats["viajes_completados"] >= 10:
            self.logros["sin_accidentes"] = True
            self.add_notif("LOGRO: Manos de seda! 10 viajes sin accidentes.")
        if not self.logros["moral_100"] and any(c.moral >= 100 for c in self.staff):
            self.logros["moral_100"] = True
            self.add_notif("LOGRO: Chofer feliz! Moral al 100%.")

    def abandonar_ruta(self, u):
        if u.chofer:
            u.chofer.contratado = False
            u.chofer.unidad = None
        u.reset()

    def parada_bus(self, u):
        p = self.recorrido[u.pos_idx]
        bajan = int(u.pasajeros * random.uniform(0.1, 0.35))
        u.pasajeros -= bajan

        suben = int(min(u.capacidad - u.pasajeros, p["dem"]))
        evento_suben = suben
        if random.random() < 0.15:
            evento_suben = int(suben * 1.5)
            self.add_notif("Hinchas subiendo! +50% pasajeros")
            
        u.pasajeros += evento_suben
        p["dem"] -= evento_suben
        self.subsidio_pendiente += evento_suben * 620

        SND_PUERTA.play()
        if evento_suben > 0:
            self.popups_viaje.append({"txt": f"+{evento_suben}", "x": 380, "y": 200, "t": time.time()})

    def finalizar_viaje(self, u):
        pago = u.chofer.sueldo
        self.dinero -= pago
        u.chofer.moral = max(0, u.chofer.moral - random.randint(5, 12))
        u.viajes_sin_service += 1

        recaudado = int(u.pasajeros * 620)
        self.stats["recaudado_total"] += recaudado
        self.stats["pasajeros_transportados"] += u.pasajeros
        self.stats["viajes_completados"] += 1

        self.popups_viaje.append({"txt": f"${recaudado:,}", "x": 380, "y": 200, "t": time.time()})
        self.add_notif(f"Int {u.id} terminó. Sueldo: -$ {pago}")
        
        if u.viajes_sin_service >= 10:
            u.motor_lvl = max(1, u.motor_lvl - 1)
            self.add_notif(f"Int {u.id} necesita service! Motor -1")

        u.reset()

    def hacer_service(self, u):
        costo = 50000
        if self.dinero >= costo:
            self.dinero -= costo
            self.stats["gastado_mantenimiento"] += costo
            u.viajes_sin_service = 0
            u.motor_lvl = min(5, u.motor_lvl + 1)
            self.add_notif(f"Service Int {u.id} completo!")
            SND_HIRE.play()
        else:
            self.add_notif("No te alcanza para el service")

    def lanzar_evento_ambiente(self):
        e = random.random()
        if e < 0.25 and time.time() > self.inmunidad_piquete_hasta:
            p = random.choice(self.recorrido)
            p["corte"] = True
            self.frase_terminal = f"PIQUETE: {p['n'].upper()}"
            SND_ALERT.play()
        elif e < 0.45:
            for p in self.recorrido: p["corte"] = False
            self.frase_terminal = "Ruta libre, dale!"
        elif e < 0.55:
            self.frase_terminal = "LLUVIA: +50% demanda!"
            for p in self.recorrido:
                p["dem"] = min(100, p["dem"] * 1.5)

        self.timer_radio = 5

    def add_notif(self, m):
        self.notificaciones.append({"m": m, "t": time.time()})

    def despachar(self):
        u_l = [u for u in self.unidades if u.pos_idx == -1]
        c_l = [c for c in self.staff if not c.unidad and c.cansancio < 85 and c.moral > 20]
        if u_l and c_l:
            u, c = u_l[0], c_l[0]
            u.pos_idx = 0
            u.progreso = 0.0
            u.chofer = c
            c.unidad = u
            u.ruta_key = self.ruta_actual
            SND_CLICK.play()
            self.add_notif(f"Int {u.id} despachado en Ruta {self.ruta_actual}!")
            self.parada_bus(u)
        else:
            self.frase_terminal = "No hay coches o choferes, boludo."

    def draw_btn(self, rect, txt, col, col_text=C_WHITE):
        pygame.draw.rect(screen, col, rect, border_radius=14)
        pygame.draw.rect(screen, C_WHITE, rect, 2, border_radius=14)
        s = FONT_S.render(txt, True, col_text)
        screen.blit(s, s.get_rect(center=rect.center))

    def draw_btn_small(self, rect, txt, col, col_text=C_WHITE):
        pygame.draw.rect(screen, col, rect, border_radius=12)
        pygame.draw.rect(screen, C_WHITE, rect, 2, border_radius=12)
        s = FONT_MS.render(txt, True, col_text)
        screen.blit(s, s.get_rect(center=rect.center))

    def dibujar_bondi_pro(self, x, y, u):
        oy = math.sin(u.oscilar) * 4
        color_cuerpo = C_GOLD if u.motor_lvl >= 4 else C_ORANGE if u.motor_lvl >= 2 else C_YELLOW
        if u.averiado > 0 and int(time.time()*6)%2==0:
            color_cuerpo = C_RED
            
        pygame.draw.ellipse(screen, (20,20,20), (x+10, y+55+oy, 180, 18))
        pygame.draw.rect(screen, color_cuerpo, (x, y+oy, 200, 60), border_radius=12)
        pygame.draw.rect(screen, C_DARK, (x, y+oy, 200, 60), 3, border_radius=12)

        for i in range(4):
            pygame.draw.rect(screen, (120, 200, 255), (x+15 + i*45, y+10+oy, 35, 22), border_radius=4)

        pygame.draw.circle(screen, (40,40,40), (x+40, y+65+oy), 14)
        pygame.draw.circle(screen, (40,40,40), (x+160, y+65+oy), 14)
        pygame.draw.circle(screen, C_GRAY, (x+40, y+65+oy), 7)
        pygame.draw.circle(screen, C_GRAY, (x+160, y+65+oy), 7)

        screen.blit(FONT_MS.render(f"I-{u.id}", True, C_DARK), (x+15, y+35+oy))
        pct = u.pasajeros / u.capacidad
        pygame.draw.rect(screen, C_DARK, (x+70, y+42+oy, 110, 9))
        pygame.draw.rect(screen, C_GREEN if pct < 0.8 else C_RED, (x+70, y+42+oy, int(110*pct), 9))

        if u.chofer:
            pygame.draw.rect(screen, C_RED, (x, y-15+oy, int(200 * (u.chofer.cansancio/100)), 5))
            pygame.draw.rect(screen, C_PURPLE, (x, y-24+oy, int(200 * (u.chofer.moral/100)), 5))

    def dibujar_menu(self):
        es_noche = 22 <= self.hora or self.hora < 6
        screen.fill(C_BG_NOCHE if es_noche else C_BG_DIA)

        for i in range(16):
            alpha = 30 + i*5
            s = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
            s.fill((*C_ACCENT, alpha))
            screen.blit(s, (0, i*80))

        titulo = FONT_XL.render("LÍNEA 55", True, C_GOLD)
        sub = FONT_L.render("TYCOON", True, C_ACCENT)
        screen.blit(titulo, (WIDTH//2 - titulo.get_width()//2, 140))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 210))

        self.btns_menu = []
        opciones = [("VAMO A JUGA", C_GREEN), ("LOGROS", C_PURPLE), ("OPCIONES", C_ORANGE), ("SALIR", C_RED)]

        for i, (txt, col) in enumerate(opciones):
            btn = pygame.Rect(WIDTH//2-170, 320 + i*110, 340, 85)
            self.draw_btn(btn, txt, col, C_DARK)
            self.btns_menu.append((btn, txt))

        screen.blit(FONT_MS.render("v15.0 - La Matanza Edition", True, C_GRAY), (20, HEIGHT-45))

    def dibujar_logros(self):
        screen.fill(C_DARK)
        screen.blit(FONT_L.render("LOGROS", True, C_PURPLE), (WIDTH//2-90, 70))

        y = 180
        for nombre, desbloqueado in self.logros.items():
            col = C_GOLD if desbloqueado else C_GRAY
            txt = nombre.replace("_", " ").upper()
            estado = "DESBLOQUEADO" if desbloqueado else "BLOQUEADO"
            screen.blit(FONT_M.render(txt, True, col), (40, y))
            screen.blit(FONT_S.render(estado, True, col), (40, y+45))
            y += 110

        self.btn_volver_logros = pygame.Rect(WIDTH//2-140, HEIGHT-140, 280, 75)
        self.draw_btn(self.btn_volver_logros, "VOLVER", C_ACCENT, C_DARK)

    def dibujar_opciones(self):
        screen.fill(C_DARK)
        screen.blit(FONT_L.render("OPCIONES", True, C_ORANGE), (WIDTH//2-110, 70))
        screen.blit(FONT_M.render("Resetear partida", True, C_WHITE), (40, 200))

        self.btn_reset_opc = pygame.Rect(WIDTH//2-170, 280, 340, 75)
        self.draw_btn(self.btn_reset_opc, "RESET PARTIDA", C_RED, C_WHITE)
        
        self.btn_volver_opc = pygame.Rect(WIDTH//2-140, HEIGHT-140, 280, 75)
        self.draw_btn(self.btn_volver_opc, "VOLVER", C_ACCENT, C_DARK)

    def dibujar_ui_juego(self, es_noche):
        c_ui = C_UI_NOCHE if es_noche else C_UI_DIA
        
        pygame.draw.rect(screen, c_ui, (0, 0, WIDTH, 140))
        pygame.draw.rect(screen, C_DARK, (0, 140, WIDTH, 4))
        
        screen.blit(FONT_M.render(f"$ {int(self.dinero):,}", True, C_GREEN), (20, 15))
        screen.blit(FONT_S.render(f"Subsidios: $ {self.subsidio_pendiente:,}", True, C_GOLD), (20, 60))
        
        pygame.draw.rect(screen, C_DARK, self.rect_reloj, border_radius=10)
        hora_str = f"{int(self.hora):02d}:{int((self.hora % 1) * 60):02d}"
        screen.blit(FONT_M.render(hora_str, True, C_WHITE), (self.rect_reloj.x + 25, self.rect_reloj.y + 10))
        
        self.draw_btn(self.btn_pausa_rect, "||", C_ORANGE, C_DARK)
        
        self.btn_rutas = []
        for i, (key, ruta) in enumerate(RUTAS.items()):
            rect = pygame.Rect(20 + i*110, 95, 100, 35)
            col = C_ACCENT if self.ruta_actual == key else (C_GRAY if not ruta["desbloqueada"] else C_DARK)
            self.draw_btn_small(rect, f"Ruta {key}", col)
            self.btn_rutas.append((rect, key, ruta))

        pygame.draw.rect(screen, c_ui, (0, 1160, WIDTH, 120))
        pygame.draw.rect(screen, C_DARK, (0, 1156, WIDTH, 4))
        
        self.draw_btn(self.btn_mapa, "MAPA", C_ACCENT if self.vista == "MAPA" else C_GRAY)
        self.draw_btn(self.btn_staff, "STAFF", C_PURPLE if self.vista == "STAFF" else C_GRAY)
        self.draw_btn(self.btn_taller, "TALLER", C_ORANGE if self.vista == "TALLER" else C_GRAY)
        self.draw_btn(self.btn_despachar, "SALIR", C_RED)
        self.draw_btn(self.btn_cobrar, "COBRAR", C_GREEN)
        
        pygame.draw.rect(screen, C_CHOFER_MSG, self.rect_chofer_msg, border_radius=10)
        pygame.draw.rect(screen, C_GRAY, self.rect_chofer_msg, 2, border_radius=10)
        y_msg = self.rect_chofer_msg.y + 10
        for m in self.mensajes_chofer[-3:]:
            screen.blit(FONT_S.render(m["m"], True, C_WHITE), (self.rect_chofer_msg.x + 10, y_msg))
            y_msg += 25

    def dibujar_mapa(self):
        # Clipping para que el mapa no tape la interfaz de arriba y abajo (Fix Bug Map)
        clip_rect = pygame.Rect(0, 144, WIDTH, 1012)
        screen.set_clip(clip_rect)

        y_base = 160 + self.scroll_y
        pygame.draw.rect(screen, (40, 40, 45), (120, y_base, 20, len(self.recorrido) * 140))
        
        for i, p in enumerate(self.recorrido):
            y_parada = y_base + i * 140
            col_parada = C_RED if p["corte"] else C_WHITE
            pygame.draw.circle(screen, col_parada, (130, y_parada), 15)
            pygame.draw.circle(screen, C_DARK, (130, y_parada), 15, 3)
            screen.blit(FONT_MS.render(p["n"], True, C_WHITE), (160, y_parada - 10))
            
            dem_rect = pygame.Rect(160, y_parada + 15, p["dem"], 10)
            pygame.draw.rect(screen, C_GREEN if p["dem"] < 50 else C_ORANGE, dem_rect)

        for u in self.unidades:
            if u.pos_idx != -1 and u.ruta_key == self.ruta_actual:
                y_bondi = y_base + u.pos_idx * 140 + (u.progreso * 140)
                self.dibujar_bondi_pro(180, y_bondi - 30, u)

        screen.set_clip(None) # Reseteamos clip

    def dibujar_staff(self):
        screen.blit(FONT_L.render("MERCADO", True, C_PURPLE), (40, 160))
        self.btns_hire = []
        y = 220
        for i, c in enumerate(self.bolsa):
            if i > 3: break
            pygame.draw.rect(screen, C_MSG_BG, (20, y, WIDTH//2-30, 90), border_radius=10)
            screen.blit(FONT_MS.render(f"{c.nombre} ({c.personalidad})", True, C_WHITE), (30, y+10))
            screen.blit(FONT_S.render(f"${c.sueldo}", True, C_GREEN), (30, y+35))
            btn = pygame.Rect(30, y+60, 100, 25)
            self.draw_btn_small(btn, "80K", C_ACCENT)
            self.btns_hire.append((btn, c))
            y += 100

        screen.blit(FONT_L.render("PLANTEL", True, C_ORANGE), (WIDTH//2 + 20, 160))
        self.btns_fire = []
        y = 220
        for i, c in enumerate(self.staff):
            if i + (self.scroll_y // -100) > len(self.staff): break
            pygame.draw.rect(screen, C_MSG_BG, (WIDTH//2 + 10, y, WIDTH//2-30, 90), border_radius=10)
            screen.blit(FONT_MS.render(f"{c.nombre}", True, C_WHITE), (WIDTH//2 + 20, y+10))
            
            pygame.draw.rect(screen, C_PURPLE, (WIDTH//2 + 20, y+40, int(c.moral), 8))
            pygame.draw.rect(screen, C_RED, (WIDTH//2 + 20, y+55, int(c.cansancio), 8))
            
            btn = pygame.Rect(WIDTH//2 + 140, y+60, 80, 25)
            self.draw_btn_small(btn, "RAJAR", C_RED)
            self.btns_fire.append((btn, c))
            y += 100

    def dibujar_taller(self):
        self.btns_upg = []
        for i, u in enumerate(self.unidades):
            x = 30 + (i % 2) * 340
            y = 160 + (i // 2) * 160 + self.scroll_y
            
            pygame.draw.rect(screen, C_MSG_BG, (x, y, 320, 140), border_radius=10)
            screen.blit(FONT_M.render(f"Int {u.id}", True, C_GOLD), (x+10, y+10))
            screen.blit(FONT_S.render(f"Ruta: {u.ruta_key}", True, C_WHITE), (x+100, y+15))
            
            screen.blit(FONT_S.render(f"M: Lvl {u.motor_lvl}", True, C_WHITE), (x+10, y+50))
            screen.blit(FONT_S.render(f"F: Lvl {u.frenos_lvl}", True, C_WHITE), (x+10, y+80))
            
            costo_m = u.motor_lvl * 20000
            costo_f = u.frenos_lvl * 15000
            
            if u.motor_lvl < 5:
                btn_m = pygame.Rect(x+110, y+50, 80, 25)
                self.draw_btn_small(btn_m, f"${costo_m//1000}k", C_ACCENT)
                self.btns_upg.append((btn_m, u, "m", costo_m))
                
            if u.frenos_lvl < 5:
                btn_f = pygame.Rect(x+110, y+80, 80, 25)
                self.draw_btn_small(btn_f, f"${costo_f//1000}k", C_ACCENT)
                self.btns_upg.append((btn_f, u, "f", costo_f))
                
            btn_srv = pygame.Rect(x+200, y+50, 100, 55)
            col_srv = C_RED if u.viajes_sin_service >= 8 else C_GREEN
            self.draw_btn_small(btn_srv, "SERVICE", col_srv)
            self.btns_upg.append((btn_srv, u, "s", 50000))

    def dibujar_pausa(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        screen.blit(s, (0, 0))
        
        rect = pygame.Rect(50, 150, WIDTH-100, HEIGHT-300)
        pygame.draw.rect(screen, C_UI_NOCHE, rect, border_radius=20)
        pygame.draw.rect(screen, C_ORANGE, rect, 3, border_radius=20)
        
        screen.blit(FONT_XL.render("PAUSA", True, C_ORANGE), (WIDTH//2 - 90, 180))
        
        y = 280
        for k, v in self.stats.items():
            txt = k.replace("_", " ").upper()
            val = f"${v:,}" if "recaudado" in k or "gastado" in k else str(v)
            screen.blit(FONT_S.render(f"{txt}: {val}", True, C_WHITE), (80, y))
            y += 40
            
        self.btn_reset_opc = pygame.Rect(WIDTH//2-140, HEIGHT-250, 280, 60)
        self.draw_btn(self.btn_reset_opc, "REINICIAR TODO", C_RED)

    def dibujar_evento_popup(self):
        if not self.evento_popup_actual: return
        
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 210))
        screen.blit(s, (0, 0))
        
        ev = self.evento_popup_actual
        rect = pygame.Rect(40, HEIGHT//2 - 250, WIDTH - 80, 500)
        pygame.draw.rect(screen, C_UI_NOCHE, rect, border_radius=20)
        pygame.draw.rect(screen, C_ORANGE, rect, 4, border_radius=20)
        
        # Título
        tit = FONT_M.render(ev["titulo"], True, C_ORANGE)
        screen.blit(tit, tit.get_rect(center=(WIDTH//2, rect.y + 40)))
        
        # Texto Descriptivo
        y_txt = rect.y + 110
        for linea in ev["txt"]:
            l_rnd = FONT_MS.render(linea, True, C_WHITE)
            screen.blit(l_rnd, l_rnd.get_rect(center=(WIDTH//2, y_txt)))
            y_txt += 30
            
        # Botones de Opciones
        self.btns_evento_opciones = []
        y_btn = rect.y + 220
        colores_btn = [C_ACCENT, C_GREEN, C_RED]
        
        for idx, opc_txt in enumerate(ev["opciones"]):
            btn_rect = pygame.Rect(WIDTH//2 - 140, y_btn, 280, 65)
            color = colores_btn[idx % len(colores_btn)]
            self.draw_btn(btn_rect, opc_txt, color, C_DARK)
            self.btns_evento_opciones.append((btn_rect, ev["id"], idx))
            y_btn += 85

    def dibujar_notificaciones(self):
        y = 150
        for n in self.notificaciones:
            s = FONT_MS.render(n["m"], True, C_WHITE)
            r = s.get_rect(center=(WIDTH//2, y))
            pygame.draw.rect(screen, C_DARK, r.inflate(20, 10), border_radius=5)
            screen.blit(s, r)
            y += 35
            
        for p in self.popups_viaje:
            screen.blit(FONT_M.render(p["txt"], True, C_GREEN), (p["x"], p["y"]))

    def dibujar_popup_confirm(self):
        if not self.popup_type: return
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0,0,0,220))
        screen.blit(s, (0,0))

        rect = pygame.Rect(WIDTH//2-200, HEIGHT//2-100, 400, 200)
        pygame.draw.rect(screen, C_UI_NOCHE, rect, border_radius=20)
        pygame.draw.rect(screen, C_RED, rect, 3, border_radius=20)

        txt = FONT_M.render("¿Seguro que querés", True, C_WHITE)
        txt2 = FONT_M.render("reiniciar todo?", True, C_WHITE)
        screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2-40)))
        screen.blit(txt2, txt2.get_rect(center=(WIDTH//2, HEIGHT//2-5)))

        self.btn_confirm = pygame.Rect(WIDTH//2-180, HEIGHT//2+40, 160, 60)
        self.btn_cancel = pygame.Rect(WIDTH//2+20, HEIGHT//2+40, 160, 60)
        self.draw_btn(self.btn_confirm, "SI", C_RED, C_WHITE)
        self.draw_btn(self.btn_cancel, "NO", C_GREEN, C_DARK)

    def dibujar_tooltip(self):
        if not self.tooltip_data: return
        x, y, u = self.tooltip_data
        rect = pygame.Rect(x, y-120, 280, 110)
        pygame.draw.rect(screen, C_DARK, rect, border_radius=12)
        pygame.draw.rect(screen, C_GOLD, rect, 2, border_radius=12)

        lineas = [
            f"Chofer: {u.chofer.nombre if u.chofer else 'Ninguno'}",
            f"Moral: {int(u.chofer.moral)}%" if u.chofer else "Moral: --",
            f"Cansancio: {int(u.chofer.cansancio)}%" if u.chofer else "Cansancio: --",
            f"Pax: {u.pasajeros}/{u.capacidad}"
        ]

        for i, linea in enumerate(lineas):
            screen.blit(FONT_MS.render(linea, True, C_WHITE), (x+10, y-115+i*22))
            
    def dibujar_tutorial(self):
        if self.tutorial_idx < len(self.tutorial_msgs):
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            screen.blit(s, (0, 0))
            
            rect = pygame.Rect(50, HEIGHT//2 - 100, WIDTH - 100, 200)
            pygame.draw.rect(screen, C_UI_DIA, rect, border_radius=15)
            
            txt = FONT_M.render("TUTORIAL", True, C_GOLD)
            screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2 - 60)))
            
            msg = FONT_MS.render(self.tutorial_msgs[self.tutorial_idx], True, C_WHITE)
            screen.blit(msg, msg.get_rect(center=(WIDTH//2, HEIGHT//2)))
            
            screen.blit(FONT_S.render("Click para continuar", True, C_GRAY), (WIDTH//2 - 80, HEIGHT//2 + 60))

    def dibujar_game_over(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((100, 0, 0, 220))
        screen.blit(s, (0, 0))
        
        txt = FONT_XL.render("BANCARROTA", True, C_WHITE)
        txt2 = FONT_M.render("Llegaste a -$200.000", True, C_GRAY)
        screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
        screen.blit(txt2, txt2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
        
        self.btn_reset_opc = pygame.Rect(WIDTH//2-140, HEIGHT//2 + 100, 280, 60)
        self.draw_btn(self.btn_reset_opc, "REINICIAR PARTIDA", C_ORANGE)

    def dibujar(self):
        if self.estado == "MENU":
            self.dibujar_menu()
        elif self.estado == "LOGROS":
            self.dibujar_logros()
        elif self.estado == "OPCIONES":
            self.dibujar_opciones()
        elif self.estado == "JUEGO":
            es_noche = 22 <= self.hora or self.hora < 6
            screen.fill(C_BG_NOCHE if es_noche else C_BG_DIA)
            
            if self.vista == "MAPA": self.dibujar_mapa()
            elif self.vista == "STAFF": self.dibujar_staff()
            elif self.vista == "TALLER": self.dibujar_taller()

            self.dibujar_ui_juego(es_noche)
            self.dibujar_notificaciones()
            
            if self.pausa: self.dibujar_pausa()
            if self.game_over: self.dibujar_game_over()
            self.dibujar_tutorial()
            self.dibujar_popup_confirm()
            self.dibujar_tooltip()
            
            if self.evento_popup_actual:
                self.dibujar_evento_popup()

    def guardar_partida(self):
        data = {
            "dinero": self.dinero,
            "subsidio": self.subsidio_pendiente,
            "hora": self.hora,
            "ruta": self.ruta_actual,
            "unidades": [u.to_dict() for u in self.unidades],
            "staff": [c.to_dict() for c in self.staff],
            "logros": self.logros,
            "stats": self.stats,
            "rutas": {k: v["desbloqueada"] for k, v in RUTAS.items()}
        }
        with open("save_v15.json", "w") as f:
            json.dump(data, f)

    def cargar_partida(self):
        if not os.path.exists("save_v15.json"): return
        try:
            with open("save_v15.json", "r") as f:
                data = json.load(f)
                self.dinero = data.get("dinero", 600000)
                self.subsidio_pendiente = data.get("subsidio", 0)
                self.hora = data.get("hora", 4.0)
                self.ruta_actual = data.get("ruta", "A")
                self.logros = data.get("logros", self.logros)
                self.stats = data.get("stats", self.stats)
                
                if "unidades" in data:
                    for i, udata in enumerate(data["unidades"]):
                        u = self.unidades[i]
                        u.motor_lvl = udata.get("m", 1)
                        u.frenos_lvl = udata.get("f", 1)
                        u.viajes_sin_service = udata.get("viajes", 0)
                if "staff" in data:
                    for i, cdata in enumerate(data["staff"]):
                        if i < len(self.staff):
                            self.staff[i].moral = cdata.get("m", 85)
                            self.staff[i].cansancio = cdata.get("c", 0)
                if "rutas" in data:
                    for k, v in data["rutas"].items():
                        if k in RUTAS: RUTAS[k]["desbloqueada"] = v
        except: pass

    def main(self):
        corriendo = True
        drag = False
        while corriendo:
            dt = CLOCK.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.guardar_partida()
                    corriendo = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    SND_CLICK.play()

                    if self.estado == "MENU":
                        for btn, txt in self.btns_menu:
                            if btn.collidepoint(pos):
                                if txt == "VAMO A JUGA": self.estado = "JUEGO"
                                if txt == "LOGROS": self.estado = "LOGROS"
                                if txt == "OPCIONES": self.estado = "OPCIONES"
                                if txt == "SALIR": corriendo = False

                    elif self.estado == "LOGROS":
                        if self.btn_volver_logros and self.btn_volver_logros.collidepoint(pos):
                            self.estado = "MENU"

                    elif self.estado == "OPCIONES":
                        if self.btn_volver_opc and self.btn_volver_opc.collidepoint(pos):
                            self.estado = "MENU"
                        if self.btn_reset_opc and self.btn_reset_opc.collidepoint(pos):
                            self.popup_type = "reset"

                    elif self.estado == "JUEGO":
                        # Prioridad 1: Manejar el Popup de Evento (Bloquea todo el resto)
                        if self.evento_popup_actual:
                            for btn, e_id, e_idx in self.btns_evento_opciones:
                                if btn.collidepoint(pos):
                                    self.aplicar_efecto_evento(e_id, e_idx)
                                    self.evento_popup_actual = None
                            continue # Salteamos el resto de los chequeos para simular pausa interactiva

                        if self.popup_type:
                            if self.btn_confirm and self.btn_confirm.collidepoint(pos):
                                self.reiniciar_todo()
                                self.popup_type = None
                                self.estado = "MENU"
                            if self.btn_cancel and self.btn_cancel.collidepoint(pos):
                                self.popup_type = None
                            continue

                        if self.tutorial_idx < len(self.tutorial_msgs):
                            self.tutorial_idx += 1
                            continue

                        if self.game_over:
                            if self.btn_reset_opc and self.btn_reset_opc.collidepoint(pos):
                                self.reiniciar_todo()
                            continue

                        if self.btn_pausa_rect.collidepoint(pos):
                            self.pausa = not self.pausa
                            continue

                        if self.pausa:
                            if self.btn_reset_opc and self.btn_reset_opc.collidepoint(pos):
                                self.popup_type = "reset"
                            continue

                        if self.btn_mapa.collidepoint(pos): self.vista = "MAPA"
                        if self.btn_staff.collidepoint(pos): self.vista = "STAFF"
                        if self.btn_taller.collidepoint(pos): self.vista = "TALLER"
                        if self.btn_despachar.collidepoint(pos): self.despachar()
                        
                        if self.btn_cobrar.collidepoint(pos):
                            self.dinero += self.subsidio_pendiente
                            self.subsidio_pendiente = 0
                            SND_COBRO.play()

                        for btn, key, ruta in self.btn_rutas:
                            if btn.collidepoint(pos):
                                if ruta["desbloqueada"]:
                                    self.ruta_actual = key
                                    self.actualizar_recorrido()
                                elif self.dinero >= ruta["costo"]:
                                    self.dinero -= ruta["costo"]
                                    ruta["desbloqueada"] = True
                                    self.ruta_actual = key
                                    self.actualizar_recorrido()
                                    SND_HIRE.play()

                        if self.vista == "STAFF":
                            for btn, c in self.btns_hire:
                                if btn.collidepoint(pos) and self.dinero >= 80000:
                                    self.dinero -= 80000
                                    self.bolsa.remove(c)
                                    c.contratado = True
                                    self.staff.append(c)
                                    SND_HIRE.play()

                            for btn, c in self.btns_fire:
                                if btn.collidepoint(pos):
                                    self.staff.remove(c)
                                    self.add_notif(f"Rajaste a {c.nombre}. Que te garúe finito.")

                        if self.vista == "TALLER":
                            for btn, u, tipo, costo in self.btns_upg:
                                if btn.collidepoint(pos):
                                    if tipo == "s":
                                        self.hacer_service(u)
                                    elif self.dinero >= costo:
                                        self.dinero -= costo
                                        if tipo == "m": u.motor_lvl += 1
                                        else: u.frenos_lvl += 1
                                        self.add_notif(f"Int {u.id} a Lvl {u.motor_lvl if tipo=='m' else u.frenos_lvl}")
                                        SND_HIRE.play()

                        if self.vista == "MAPA":
                            # Solo detectar clic en bondis si caen dentro del área visible scrolleada
                            clip_rect_mapa = pygame.Rect(0, 144, WIDTH, 1012)
                            if clip_rect_mapa.collidepoint(pos):
                                for u in self.unidades:
                                    if u.pos_idx != -1 and u.ruta_key == self.ruta_actual:
                                        y_bondi = 160 + self.scroll_y + u.pos_idx * 140 + (u.progreso * 140)
                                        rect = pygame.Rect(180, y_bondi - 30, 200, 60)
                                        if rect.collidepoint(pos):
                                            self.tooltip_data = (pos[0], pos[1], u)
                                            self.tooltip_timer = 3.0

                if event.type == pygame.MOUSEBUTTONUP:
                    drag = False

                if event.type == pygame.MOUSEMOTION:
                    # Bloquear scrolleo si hay evento activo
                    if event.buttons[0] and not self.evento_popup_actual and not self.pausa:
                        drag = True
                        lim = min(0, -((len(self.recorrido) * 140 + 380) - HEIGHT))
                        self.scroll_y = max(lim, min(0, self.scroll_y + event.rel[1]))

            self.simular(dt)
            self.dibujar()
            pygame.display.flip()

if __name__ == "__main__":
    Juego().main()
