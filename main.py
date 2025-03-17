import pygame
import sys
import os
import random
import math

# Inisialisasi Pygame
pygame.init()

# Konstanta
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Warna
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# State permainan
TITLE_SCREEN = -1
ROUND_PREP = 0
FIGHTING = 1
ROUND_OVER = 2
MATCH_RESULT = 3  # State baru untuk hasil akhir pertandingan

# Animasi state
IDLE = "idle"
RUN = "run"
JUMP = "jump"
FALL = "fall"
ATTACK1 = "attack1"
ATTACK2 = "attack2"
ATTACK3 = "attack3"
TAKE_HIT = "take_hit"
DEATH = "death"

class ParallaxBackground:
    def __init__(self):
        self.layers = []
        self.scroll = 0
        
        # Load background layers
        try:
            bg_path = os.path.join("assets", "background", "parallax_demon_woods_pack", "layers")
            layer_files = ["parallax-demon-woods-bg.png",
                         "parallax-demon-woods-far-trees.png",
                         "parallax-demon-woods-mid-trees.png",
                         "parallax-demon-woods-close-trees.png"]
            
            self.layers = []
            for i, file in enumerate(layer_files):
                img = pygame.image.load(os.path.join(bg_path, file)).convert_alpha()
                # Scale image to fit screen height while maintaining aspect ratio
                scale = SCREEN_HEIGHT / img.get_height()
                new_width = int(img.get_width() * scale)
                img = pygame.transform.scale(img, (new_width, SCREEN_HEIGHT))
                
                # Parallax speed decreases for background layers
                speed = 0.2 + (i * 0.2)  # 0.2, 0.4, 0.6, 0.8
                self.layers.append({
                    "image": img,
                    "speed": speed,
                    "pos": 0
                })
        
        except pygame.error as e:
            print(f"Couldn't load background images: {e}")
            # Fallback to solid color if images not found
            self.layers = []
    
    def update(self, player_velocity):
        self.scroll += player_velocity * 0.1
        
    def draw(self, screen):
        if not self.layers:
            screen.fill((100, 150, 200))  # Fallback sky blue color
            return
            
        for layer in self.layers:
            # Calculate how many times we need to tile the image
            image_width = layer["image"].get_width()
            tiles = math.ceil(SCREEN_WIDTH / image_width) + 2
            
            for i in range(tiles):
                # Calculate x position with parallax effect
                x = (i * image_width) - int(self.scroll * layer["speed"]) % image_width
                screen.blit(layer["image"], (x, 0))

class SpriteSheet:
    def __init__(self, image, sprite_width, sprite_height):
        self.sheet = image
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        
    def get_sprite(self, frame, scale=1):
        image = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (frame * self.sprite_width, 0, self.sprite_width, self.sprite_height))
        if scale != 1:
            new_width = int(self.sprite_width * scale)
            new_height = int(self.sprite_height * scale)
            image = pygame.transform.scale(image, (new_width, new_height))
        return image

class CharacterSprites:
    def __init__(self, character_type):
        self.animations = {}
        self.frame_counts = {}
        self.current_frame = 0
        self.animation_speed = 0.2
        self.animation_timer = 0
        
        # Load sprite sheets
        sprite_path = "assets/Huntress/Sprites" if character_type == "huntress" else "assets/EVil Wizard 2/Sprites"
        scale = 2.5 if character_type == "huntress" else 2.0
        
        # Load dan setup semua animasi
        animations_data = {
            IDLE: ("Idle.png", 8),
            RUN: ("Run.png", 8),
            JUMP: ("Jump.png", 2),
            FALL: ("Fall.png", 2),
            ATTACK1: ("Attack1.png", 5),
            ATTACK2: ("Attack2.png", 5),
            DEATH: ("Death.png", 8),
            TAKE_HIT: ("Take hit.png", 3)
        }
        
        if character_type == "huntress":
            animations_data[ATTACK3] = ("Attack3.png", 7)
        
        for anim_name, (filename, frames) in animations_data.items():
            path = os.path.join(sprite_path, filename)
            try:
                sheet = pygame.image.load(path).convert_alpha()
                width = sheet.get_width() // frames
                height = sheet.get_height()
                sprite_sheet = SpriteSheet(sheet, width, height)
                
                self.animations[anim_name] = [
                    sprite_sheet.get_sprite(i, scale) for i in range(frames)
                ]
                self.frame_counts[anim_name] = frames
            except pygame.error as e:
                print(f"Couldn't load animation {filename}: {e}")
                
        self.current_animation = IDLE
        
    def get_current_frame(self, flipped=False):
        frame = self.animations[self.current_animation][int(self.current_frame)]
        if flipped:
            frame = pygame.transform.flip(frame, True, False)
        return frame
    
    def update_animation(self, animation_name, dt):
        if animation_name != self.current_animation:
            self.current_animation = animation_name
            self.current_frame = 0
            self.animation_timer = 0
        else:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % self.frame_counts[self.current_animation]
    
    def is_animation_finished(self):
        return int(self.current_frame) >= self.frame_counts[self.current_animation] - 1

class Weapon(pygame.sprite.Sprite):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        # Sesuaikan ukuran dan posisi senjata berdasarkan karakter
        if isinstance(owner, Fighter) and owner.player_num == 1:
            # Huntress weapon (spear)
            self.image = pygame.Surface((60, 20), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, YELLOW, [(0, 10), (50, 5), (60, 10), (50, 15)])
        else:
            # Evil Wizard weapon (magic)
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (148, 0, 211), (20, 20), 20)  # Purple magic
            
        self.rect = self.image.get_rect()
        self.active = False
        self.attack_timer = 0
        self.attack_duration = 20
        
    def update(self):
        if self.active:
            self.attack_timer += 1
            if self.attack_timer >= self.attack_duration:
                self.active = False
                self.attack_timer = 0
                
        # Update posisi senjata
        if isinstance(self.owner, Fighter):
            if self.owner.player_num == 1:  # Huntress
                if self.owner.facing_right:
                    self.rect.left = self.owner.rect.right - 20
                else:
                    self.rect.right = self.owner.rect.left + 20
                self.rect.centery = self.owner.rect.centery
            else:  # Evil Wizard
                self.rect.centerx = self.owner.rect.centerx
                self.rect.centery = self.owner.rect.centery - 30

    def attack(self):
        if not self.active:
            self.active = True
            self.attack_timer = 0

class Fighter(pygame.sprite.Sprite):
    def __init__(self, x, y, player_num):
        super().__init__()
        self.player_num = player_num
        self.sprites = CharacterSprites("huntress" if player_num == 1 else "evil_wizard")
        self.image = self.sprites.get_current_frame()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Collision box yang lebih kecil dan sesuai dengan karakter
        self.hit_box = pygame.Rect(0, 0, 40, 50)  # Kurangi tinggi hit box lagi
        self.update_hit_box()
        
        # Status fighter
        self.health = 100
        self.max_health = 100
        self.energy = 100
        self.max_energy = 100
        self.ultimate_gauge = 0
        self.max_ultimate = 100
        self.velocity_x = 0
        self.velocity_y = 0
        self.jumping = False
        self.ground_y = y + 10  # Sesuaikan ground_y dengan posisi spawn
        self.attacking = False
        self.attack_type = 0
        self.attack_timer = 0
        self.attack_cooldown = 30
        self.skill_cooldowns = {
            1: 0,  # Skill 1 cooldown
            2: 0,  # Skill 2 cooldown
            3: 0   # Ultimate cooldown
        }
        self.max_skill_cooldown = {
            1: 120,  # 2 detik
            2: 180,  # 3 detik
            3: 300   # 5 detik
        }
        self.skill_energy_cost = {
            1: 20,  # Skill 1 energy cost
            2: 30,  # Skill 2 energy cost
            3: 50   # Ultimate energy cost
        }
        self.energy_regen_rate = 0.2
        self.ultimate_gain_rate = 0.1
        
        self.facing_right = player_num == 2
        self.is_dead = False
        self.death_animation_started = False
        self.current_state = IDLE
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 30
        
        # Senjata
        self.weapon = Weapon(self)

    def update_hit_box(self):
        self.hit_box.centerx = self.rect.centerx
        self.hit_box.bottom = self.rect.bottom
        
    def move(self):
        if self.is_dead:
            return
            
        # Update posisi horizontal
        self.rect.x += self.velocity_x
        self.update_hit_box()
        
        # Batasi pergerakan horizontal
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            
        # Update posisi vertikal dengan gravitasi
        self.velocity_y += 0.5  # Kurangi kekuatan gravitasi
        self.rect.y += self.velocity_y
        
        # Collision dengan tanah
        if self.rect.bottom > self.ground_y:
            self.rect.bottom = self.ground_y
            self.velocity_y = 0
            self.jumping = False
        
        self.update_hit_box()

        # Update arah hadap karakter
        if self.velocity_x > 0:
            self.facing_right = True
        elif self.velocity_x < 0:
            self.facing_right = False
            
        # Update cooldowns dan resources
        for skill in self.skill_cooldowns:
            if self.skill_cooldowns[skill] > 0:
                self.skill_cooldowns[skill] -= 1
                
        # Energy regeneration
        if self.energy < self.max_energy:
            self.energy = min(self.max_energy, self.energy + self.energy_regen_rate)
            
        # Ultimate gauge build-up
        if self.ultimate_gauge < self.max_ultimate and not self.is_dead:
            self.ultimate_gauge = min(self.max_ultimate, self.ultimate_gauge + self.ultimate_gain_rate)
            
        # Update invincibility
        if self.invincible:
            self.invincible_timer += 1
            if self.invincible_timer >= self.invincible_duration:
                self.invincible = False
                self.invincible_timer = 0

    def update_animation_state(self):
        if self.is_dead:
            new_state = DEATH
        elif self.attacking:
            new_state = ATTACK1
        elif self.velocity_y < 0:
            new_state = JUMP
        elif self.velocity_y > 1:
            new_state = FALL
        elif self.velocity_x != 0:
            new_state = RUN
        else:
            new_state = IDLE
            
        self.sprites.update_animation(new_state, 1/FPS)
        self.current_state = new_state
        
        if self.current_state == ATTACK1 and self.sprites.is_animation_finished():
            self.attacking = False

    def jump(self):
        if not self.jumping and not self.is_dead:
            self.jumping = True
            self.velocity_y = -12  # Kurangi kekuatan lompatan

    def attack(self):
        if not self.is_dead and not self.attacking and self.attack_timer <= 0:
            self.attacking = True
            self.attack_timer = self.attack_cooldown
            self.weapon.attack()

    def take_damage(self, amount):
        if not self.is_dead and not self.invincible:
            self.health -= amount
            self.invincible = True
            if self.health <= 0:
                self.health = 0
                self.die()
            else:
                self.sprites.update_animation(TAKE_HIT, 1/FPS)

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.death_animation_started = True
            self.velocity_x = 0
            self.velocity_y = 0

    def update(self):
        if self.attack_timer > 0:
            self.attack_timer -= 1
            
        self.move()
        self.update_animation_state()
        self.image = self.sprites.get_current_frame(not self.facing_right)
        
        # Update resources
        if self.energy < self.max_energy:
            self.energy = min(self.max_energy, self.energy + self.energy_regen_rate)
            
        if self.ultimate_gauge < self.max_ultimate and not self.is_dead:
            self.ultimate_gauge = min(self.max_ultimate, self.ultimate_gauge + self.ultimate_gain_rate)
        
        # Buat karakter berkedip saat invincible
        if self.invincible and (self.invincible_timer // 3) % 2 == 0:
            self.image.set_alpha(128)
        else:
            self.image.set_alpha(255)
            
        self.weapon.update()

    def draw_status_bars(self, screen, is_player_one):
        # Navbar style status bars
        bar_height = 20
        health_width = 200
        energy_width = 150
        ultimate_width = 100
        padding = 10
        
        if is_player_one:
            base_x = padding
        else:
            base_x = SCREEN_WIDTH - health_width - padding
            
        base_y = padding
        
        # Health bar
        pygame.draw.rect(screen, RED, (base_x, base_y, health_width, bar_height))
        health_percent = self.health / self.max_health
        pygame.draw.rect(screen, GREEN, (base_x, base_y, health_width * health_percent, bar_height))
        
        # Energy bar
        energy_x = base_x if is_player_one else SCREEN_WIDTH - energy_width - padding
        energy_y = base_y + bar_height + 5
        pygame.draw.rect(screen, (50, 50, 255), (energy_x, energy_y, energy_width, bar_height))
        energy_percent = self.energy / self.max_energy
        pygame.draw.rect(screen, (100, 100, 255), (energy_x, energy_y, energy_width * energy_percent, bar_height))
        
        # Ultimate gauge
        ultimate_x = base_x if is_player_one else SCREEN_WIDTH - ultimate_width - padding
        ultimate_y = energy_y + bar_height + 5
        pygame.draw.rect(screen, (255, 200, 0), (ultimate_x, ultimate_y, ultimate_width, bar_height))
        ultimate_percent = self.ultimate_gauge / self.max_ultimate
        pygame.draw.rect(screen, (255, 255, 0), (ultimate_x, ultimate_y, ultimate_width * ultimate_percent, bar_height))

    def use_skill(self, skill_num):
        if not self.is_dead and not self.attacking and self.skill_cooldowns[skill_num] <= 0:
            # Check energy cost
            if self.energy >= self.skill_energy_cost[skill_num]:
                # Ultimate requires full gauge
                if skill_num == 3 and self.ultimate_gauge < self.max_ultimate:
                    return
                    
                self.attacking = True
                self.attack_type = skill_num
                self.attack_timer = self.attack_cooldown
                self.skill_cooldowns[skill_num] = self.max_skill_cooldown[skill_num]
                self.energy -= self.skill_energy_cost[skill_num]
                
                if skill_num == 3:  # Ultimate
                    self.ultimate_gauge = 0
                    self.weapon.attack()
                    # Ultimate effects - sekarang lebih terkontrol
                    self.velocity_y = -10  # Kurangi ketinggian ultimate
                    self.invincible = True
                    self.invincible_timer = 0
                elif skill_num == 1:  # Dash attack
                    self.weapon.attack()
                    self.velocity_x = 15 if self.facing_right else -15
                elif skill_num == 2:  # Jump attack
                    self.weapon.attack()
                    self.velocity_y = -8  # Kurangi ketinggian jump attack

class AIController:
    def __init__(self, fighter, target):
        self.fighter = fighter
        self.target = target
        self.decision_timer = 0
        self.current_action = None
        self.action_duration = 0
        self.difficulty = 0.7  # Tingkat kesulitan (0-1)
        self.attack_cooldown = 0
        self.skill_cooldown = 0
        
    def update(self):
        if self.fighter.is_dead:
            return
            
        self.decision_timer += 1
        if self.decision_timer >= 20:  # Update keputusan lebih cepat
            self.make_decision()
            self.decision_timer = 0
            
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1
            
        self.execute_action()
    
    def make_decision(self):
        if self.target.is_dead:
            self.current_action = None
            return
            
        distance = abs(self.target.rect.centerx - self.fighter.rect.centerx)
        vertical_distance = abs(self.target.rect.centery - self.fighter.rect.centery)
        
        # Bot akan lebih agresif
        if distance > 200:  # Jika terlalu jauh
            self.current_action = "chase"
            self.action_duration = 30
        elif distance < 150:  # Jarak serang
            # Peluang menyerang berdasarkan difficulty
            if self.attack_cooldown <= 0 and random.random() < self.difficulty:
                self.current_action = "attack"
                self.attack_cooldown = 30
                self.action_duration = 20
            
            # Gunakan skill berdasarkan difficulty
            if self.skill_cooldown <= 0 and random.random() < self.difficulty:
                skill_choice = random.randint(1, 3)
                if skill_choice == 1 and self.fighter.energy >= 20:
                    self.current_action = "skill1"
                elif skill_choice == 2 and self.fighter.energy >= 30:
                    self.current_action = "skill2"
                elif skill_choice == 3 and self.fighter.ultimate_gauge >= 100:
                    self.current_action = "ultimate"
                self.skill_cooldown = 60
        else:
            self.current_action = "chase"
            
        # Lompat untuk menghindari serangan atau mengejar
        if random.random() < self.difficulty * 0.3:
            self.fighter.jump()
    
    def execute_action(self):
        if self.current_action == "chase":
            # Bergerak lebih cepat saat mengejar
            speed = 6 if self.difficulty > 0.6 else 5
            if self.target.rect.centerx > self.fighter.rect.centerx:
                self.fighter.velocity_x = speed
            else:
                self.fighter.velocity_x = -speed
        elif self.current_action == "attack":
            self.fighter.attack()
        elif self.current_action == "skill1":
            self.fighter.use_skill(1)
        elif self.current_action == "skill2":
            self.fighter.use_skill(2)
        elif self.current_action == "ultimate":
            self.fighter.use_skill(3)
            
        self.action_duration -= 1
        if self.action_duration <= 0:
            self.current_action = None
            self.fighter.velocity_x = 0

class GameUI:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

    def draw_navbar(self, screen, player1, player2, round_timer, fps):
        # Navbar style status bars
        bar_height = 20
        health_width = 200
        energy_width = 150
        ultimate_width = 100
        padding = 10
        
        # Draw timer
        minutes = round_timer // (60 * fps)
        seconds = (round_timer % (60 * fps)) // fps
        timer_text = f"{minutes:02d}:{seconds:02d}"
        timer_surface = pygame.font.Font(None, 36).render(timer_text, True, WHITE)
        timer_rect = timer_surface.get_rect(center=(self.screen_width/2, 25))
        screen.blit(timer_surface, timer_rect)
        
        # Draw status bars
        player1.draw_status_bars(screen, True)
        player2.draw_status_bars(screen, False)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Python Fighter")
        self.clock = pygame.time.Clock()
        
        self.background = ParallaxBackground()
        self.game_state = TITLE_SCREEN
        self.difficulty_selected = False  # Tambah state untuk pilihan difficulty
        self.ai_difficulty = 0.5  # Default difficulty
        self.round_number = 1
        self.round_timer = 7200
        self.round_text = ""
        
        # Sesuaikan posisi tanah lebih rendah
        self.floor_height = SCREEN_HEIGHT - 100  # Tetap di posisi yang sama
        
        # Sistem skor dan hasil
        self.player1_wins = 0
        self.player2_wins = 0
        self.round_end_timer = 600
        self.is_draw = False
        
        # Font untuk teks
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
        self.tiny_font = pygame.font.Font(None, 24)
        
        # UI
        self.game_ui = GameUI(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Membuat fighter
        self.reset_fighters()
        
    def reset_fighters(self):
        # Sesuaikan posisi awal fighter lebih rendah
        self.player1 = Fighter(200, self.floor_height + 110, 1)
        self.player2 = Fighter(200, self.floor_height + 110, 2)
        self.ai_controller = AIController(self.player2, self.player1)
        self.ai_controller.difficulty = self.ai_difficulty  # Set difficulty level
        
        self.all_sprites = pygame.sprite.Group()
        self.weapons = pygame.sprite.Group()
        
        self.all_sprites.add(self.player1, self.player2)
        self.weapons.add(self.player1.weapon, self.player2.weapon)
        
    def reset_game(self):
        self.game_state = TITLE_SCREEN
        self.difficulty_selected = False  # Reset difficulty selection
        self.round_number = 1
        self.player1_wins = 0
        self.player2_wins = 0
        self.reset_fighters()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if self.game_state == TITLE_SCREEN:
                    if not self.difficulty_selected:
                        if event.key == pygame.K_1:  # Easy
                            self.ai_difficulty = 0.3
                            self.difficulty_selected = True
                        elif event.key == pygame.K_2:  # Medium
                            self.ai_difficulty = 0.6
                            self.difficulty_selected = True
                        elif event.key == pygame.K_3:  # Hard
                            self.ai_difficulty = 0.9
                            self.difficulty_selected = True
                    elif event.key == pygame.K_SPACE:
                        self.game_state = ROUND_PREP
                        self.round_timer = 180  # 3 detik countdown
                elif event.key == pygame.K_SPACE:
                    if self.game_state == ROUND_OVER and self.round_end_timer <= 0:
                        if self.player1_wins < 2 and self.player2_wins < 2:
                            self.start_new_round()
                    elif self.game_state == MATCH_RESULT:
                        self.reset_game()
                elif self.game_state == FIGHTING:
                    if event.key == pygame.K_SPACE:
                        self.player1.jump()
                    if event.key == pygame.K_j:
                        self.player1.attack()
                    if event.key == pygame.K_k:
                        self.player1.use_skill(1)
                    if event.key == pygame.K_l:
                        self.player1.use_skill(2)
                    if event.key == pygame.K_i:
                        self.player1.use_skill(3)
                    
        if self.game_state == FIGHTING:
            keys = pygame.key.get_pressed()
            
            self.player1.velocity_x = 0
            if keys[pygame.K_a]:
                self.player1.velocity_x = -5
            if keys[pygame.K_d]:
                self.player1.velocity_x = 5
            
        return True

    def check_collisions(self):
        for weapon in self.weapons:
            if weapon.active:
                hits = pygame.sprite.spritecollide(weapon, self.all_sprites, False)
                for hit in hits:
                    if hit != weapon.owner and not hit.is_dead:
                        hit.take_damage(10)
                        weapon.active = False

    def update(self):
        if self.game_state == TITLE_SCREEN:
            return
        elif self.game_state == ROUND_PREP:
            self.round_timer -= 1
            if self.round_timer <= 0:
                self.game_state = FIGHTING
                self.round_timer = 7200  # Reset to 2 minutes for fighting
                self.round_text = f"Round {self.round_number}"
        elif self.game_state == FIGHTING:
            self.round_timer -= 1
            if self.round_timer <= 0:
                # Time over, player with more health wins
                if self.player1.health > self.player2.health:
                    self.player2.die()
                    self.player1_wins += 1
                    self.is_draw = False
                elif self.player2.health > self.player1.health:
                    self.player1.die()
                    self.player2_wins += 1
                    self.is_draw = False
                else:
                    self.is_draw = True
                self.game_state = ROUND_OVER
                self.round_end_timer = 600  # 10 detik jeda
                
            self.all_sprites.update()
            self.weapons.update()
            self.ai_controller.update()
            self.check_collisions()
            
            self.background.update(self.player1.velocity_x)
            
            # Cek kondisi menang
            if self.player1.is_dead:
                self.player2_wins += 1
                self.is_draw = False
                self.game_state = ROUND_OVER
                self.round_end_timer = 600
            elif self.player2.is_dead:
                self.player1_wins += 1
                self.is_draw = False
                self.game_state = ROUND_OVER
                self.round_end_timer = 600
        elif self.game_state == ROUND_OVER:
            self.round_end_timer -= 1
            if self.player1_wins >= 2 or self.player2_wins >= 2:
                self.game_state = MATCH_RESULT

    def start_new_round(self):
        self.round_number += 1
        self.game_state = ROUND_PREP
        self.round_timer = 180
        
        # Reset posisi fighter dengan posisi yang baru
        self.player1.rect.x = 200
        self.player2.rect.x = 200
        self.player1.rect.y = self.floor_height + 110  # Turunkan karakter
        self.player2.rect.y = self.floor_height + 110  # Turunkan karakter
        self.player1.ground_y = self.floor_height + 112  # Sesuaikan ground_y
        self.player2.ground_y = self.floor_height + 112  # Sesuaikan ground_y
        self.player1.health = 100
        self.player2.health = 100
        self.player1.is_dead = False
        self.player2.is_dead = False
        self.player1.death_animation_started = False
        self.player2.death_animation_started = False
        self.player1.invincible = False
        self.player2.invincible = False
        self.player1.attack_timer = 0
        self.player2.attack_timer = 0

    def draw(self):
        self.background.draw(self.screen)
        # Gambar tanah yang lebih tinggi dan sesuai dengan background
        pygame.draw.rect(self.screen, (101, 67, 33), (0, self.floor_height - 20, SCREEN_WIDTH, SCREEN_HEIGHT - (self.floor_height - 20)))
        
        if self.game_state == TITLE_SCREEN:
            # Draw title
            title_text = self.font.render("PYTHON FIGHTER", True, WHITE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/3))
            self.screen.blit(title_text, title_rect)
            
            if not self.difficulty_selected:
                # Draw difficulty selection
                difficulty_text = [
                    "Pilih Tingkat Kesulitan:",
                    "1 - MUDAH",
                    "2 - SEDANG",
                    "3 - SULIT"
                ]
                
                for i, text in enumerate(difficulty_text):
                    diff_text = self.small_font.render(text, True, WHITE)
                    diff_rect = diff_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + i*30))
                    self.screen.blit(diff_text, diff_rect)
            else:
                # Draw controls info after difficulty is selected
                controls = [
                    "Kontrol:",
                    "A/D - Gerak Kiri/Kanan",
                    "SPACE - Lompat",
                    "J - Serangan Normal",
                    "K - Skill 1 (Dash Attack)",
                    "L - Skill 2 (Jump Attack)",
                    "I - Ultimate"
                ]
                
                for i, text in enumerate(controls):
                    control_text = self.small_font.render(text, True, WHITE)
                    control_rect = control_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + i*30))
                    self.screen.blit(control_text, control_rect)
                
                # Draw start instruction
                start_text = self.tiny_font.render("Tekan SPACE untuk memulai", True, YELLOW)
                start_rect = start_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 100))
                # Make it blink
                if (pygame.time.get_ticks() // 500) % 2:  # Blink every 0.5 seconds
                    self.screen.blit(start_text, start_rect)
        elif self.game_state == MATCH_RESULT:
            # Tampilkan hasil akhir pertandingan
            winner = "Player 1" if self.player1_wins > self.player2_wins else "Player 2"
            result_text = f"{winner} Memenangkan Pertandingan!"
            score_text = f"Skor: {self.player1_wins} - {self.player2_wins}"
            
            text = self.font.render(result_text, True, WHITE)
            score = self.small_font.render(score_text, True, WHITE)
            continue_text = self.tiny_font.render("Tekan SPACE untuk main lagi", True, YELLOW)
            
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
            score_rect = score.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
            continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 100))
            
            self.screen.blit(text, text_rect)
            self.screen.blit(score, score_rect)
            self.screen.blit(continue_text, continue_rect)
        else:
            # Draw UI
            self.game_ui.draw_navbar(self.screen, self.player1, self.player2, self.round_timer, FPS)
            
            # Gambar semua sprite
            self.all_sprites.draw(self.screen)
            
            # Gambar senjata aktif
            for weapon in self.weapons:
                if weapon.active:
                    self.screen.blit(weapon.image, weapon.rect)
            
            # Gambar teks ronde
            if self.game_state == ROUND_PREP:
                text = self.font.render(f"Round {self.round_number}", True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
                self.screen.blit(text, text_rect)
            elif self.game_state == ROUND_OVER:
                if self.is_draw:
                    result_text = "Seri!"
                else:
                    winner = "Player 1" if self.player2.is_dead else "Player 2"
                    result_text = f"{winner} Menang!"
                
                text = self.font.render(result_text, True, WHITE)
                score = self.small_font.render(f"Skor: {self.player1_wins} - {self.player2_wins}", True, WHITE)
                timer = self.small_font.render(f"Jeda: {self.round_end_timer//60}", True, WHITE)
                
                text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
                score_rect = score.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 20))
                timer_rect = timer.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 70))
                
                self.screen.blit(text, text_rect)
                self.screen.blit(score, score_rect)
                self.screen.blit(timer, timer_rect)
                
                if self.round_end_timer <= 0:
                    continue_text = self.tiny_font.render("Tekan SPACE untuk lanjut", True, YELLOW)
                    continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 120))
                    self.screen.blit(continue_text, continue_rect)
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit() 