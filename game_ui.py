import pygame

class GameUI:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.small_font = pygame.font.Font(None, 36)
        
    def draw_navbar(self, screen, player1, player2, round_timer, fps):
        # Draw navbar background
        navbar_height = 80
        pygame.draw.rect(screen, (40, 40, 40), (0, 0, self.screen_width, navbar_height))
        
        # Draw timer
        minutes = round_timer // (60 * fps)
        seconds = (round_timer % (60 * fps)) // fps
        timer_text = f"{minutes:02d}:{seconds:02d}"
        timer_surface = self.small_font.render(timer_text, True, (255, 255, 255))
        timer_rect = timer_surface.get_rect(center=(self.screen_width/2, 25))
        screen.blit(timer_surface, timer_rect)
        
        # Draw player status bars
        self.draw_player_status(screen, player1, True)
        self.draw_player_status(screen, player2, False)
        
    def draw_player_status(self, screen, player, is_player_one):
        # Bar dimensions
        bar_height = 20
        health_width = 200
        energy_width = 150
        ultimate_width = 100
        padding = 10
        
        # Position based on player
        if is_player_one:
            base_x = padding
        else:
            base_x = self.screen_width - health_width - padding
            
        base_y = padding
        
        # Health bar
        pygame.draw.rect(screen, (255, 0, 0), (base_x, base_y, health_width, bar_height))
        health_percent = player.health / player.max_health
        pygame.draw.rect(screen, (0, 255, 0), (base_x, base_y, health_width * health_percent, bar_height))
        
        # Energy bar
        energy_x = base_x if is_player_one else self.screen_width - energy_width - padding
        energy_y = base_y + bar_height + 5
        pygame.draw.rect(screen, (50, 50, 255), (energy_x, energy_y, energy_width, bar_height))
        energy_percent = player.energy / player.max_energy
        pygame.draw.rect(screen, (100, 100, 255), (energy_x, energy_y, energy_width * energy_percent, bar_height))
        
        # Ultimate gauge
        ultimate_x = base_x if is_player_one else self.screen_width - ultimate_width - padding
        ultimate_y = energy_y + bar_height + 5
        pygame.draw.rect(screen, (255, 200, 0), (ultimate_x, ultimate_y, ultimate_width, bar_height))
        ultimate_percent = player.ultimate_gauge / player.max_ultimate
        pygame.draw.rect(screen, (255, 255, 0), (ultimate_x, ultimate_y, ultimate_width * ultimate_percent, bar_height))
        
        # Draw skill cooldown indicators
        self.draw_skill_cooldowns(screen, player, base_x, ultimate_y + bar_height + 5) 