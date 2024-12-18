from settings import * 
from sprites import * 
from groups import AllSprites
from support import * 
from timer import Timer
from random import randint

class Menu:
    def __init__(self, display_surface):
        self.display_surface = display_surface
        self.font = pygame.font.Font('fonts/pixel_font.ttf', 55)  
        self.bg_image =  pygame.image.load('images/bg2.png')
        self.text_color = (255, 255, 255)  # Màu chữ
        self.buttons = {
            "START": pygame.Rect(540, 300, 200, 70),
            "EXIT": pygame.Rect(540,400, 200, 70)
        }

    def draw(self):
        self.display_surface.blit(self.bg_image, (0,0))
        for text, rect in self.buttons.items():
            pygame.draw.rect(self.display_surface, (100, 100, 100), rect)
            pygame.draw.rect(self.display_surface, (255, 255, 255), rect, 3)  # Viền nút
            label = self.font.render(text, True, self.text_color)
            label_rect = label.get_rect(center=rect.center)
            self.display_surface.blit(label, label_rect)
        pygame.display.update()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Nhấp chuột trái
            for text, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    return text  # Trả về tên nút được nhấn
        return None


class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Chill Shipper')
        self.clock = pygame.time.Clock()
        self.running = True
    
        #menu
        self.menu = Menu(self.display_surface)
        self.show_menu = True

        # groups 
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        # load game 
        self.load_assets()

        # timers 
        self.bee_timer = Timer(randint(800,1000), func = self.create_bee, autostart = True, repeat = True)
    
    def create_bee(self):
        Bee(frames = self.bee_frames, 
            pos = ((self.level_width + WINDOW_WIDTH),(randint(0,self.level_height))), 
            groups = (self.all_sprites, self.enemy_sprites),
            speed = randint(300,500))

    def create_bullet(self, pos, direction):
        x = pos[0] + direction * 34 if direction == 1 else pos[0] + direction * 34 - self.bullet_surf.get_width()
        Bullet(self.bullet_surf, (x, pos[1]), direction, (self.all_sprites, self.bullet_sprites))
        Fire(self.fire_surf, pos, self.all_sprites, self.player)
        self.audio['shoot'].play()

    def load_assets(self):
        # graphics 
        self.player_frames = import_folder('images', 'player')
        self.bullet_surf = import_image('images', 'gun', 'bullet')
        self.fire_surf = import_image('images', 'gun', 'fire')
        self.bee_frames = import_folder('images', 'enemies', 'bee')
        self.worm_frames = import_folder('images', 'enemies', 'worm')

        # sounds 
        self.audio = audio_importer('audio')

    def setup(self):
        tmx_map = load_pygame(join('data', 'maps', '2.tmx'))
        self.level_width = tmx_map.width * TILE_SIZE
        self.level_height = tmx_map.height * TILE_SIZE
        
        self.house_rects = []  # Danh sách các vùng "House"

        for x, y, image in tmx_map.get_layer_by_name('Main').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, (self.all_sprites, self.collision_sprites))
        
        for x, y, image in tmx_map.get_layer_by_name('Decoration').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)
        
        for obj in tmx_map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites, self.player_frames, self.create_bullet)
            if obj.name == 'Worm':
                Worm(self.worm_frames, pygame.FRect(obj.x, obj.y, obj.width, obj.height), (self.all_sprites, self.enemy_sprites))
                
        house_layer = tmx_map.get_layer_by_name('House')
        if house_layer:
            for obj in house_layer:
                house_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                self.house_rects.append(house_rect)
                
        self.audio['music'].play(loops = -1)
        
    def collision(self):    
        # bullets -> enemies 
        for bullet in self.bullet_sprites:
            sprite_collision = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
            if sprite_collision:
                self.audio['impact'].play()
                bullet.kill()
                for sprite in sprite_collision:
                    sprite.destroy()
        
        # enemies -> player
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.player.become_red()  # Chuyển nhân vật thành màu đỏ
            self.audio['impact'].play()
            self.audio['music'].stop()
            self.audio['died'].play()
            self.all_sprites.draw(self.player.rect.center)  # Vẽ lại tất cả sprites
            pygame.display.update()  # Cập nhật hiển thị để thấy nhân vật đỏ
            pygame.time.delay(1000)     
            self.show_game_over_screen()
            self.restart_game()    
            
        # player -> house
        player_rect = self.player.rect
        for house_rect in self.house_rects:
            if house_rect.colliderect(player_rect):
                self.audio['music'].stop()
                self.audio['victory'].play()
                self.show_victory_screen()
                self.restart_game()
                
    def show_game_over_screen(self):
        font = pygame.font.Font('fonts/pixel_font.ttf', 150)
        text = font.render('GAME OVER', True, (255, 0, 0))
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 3000:  # Hiển thị trong 3 giây
            self.display_surface.fill((0, 0, 0))  # Nền màu đen
            self.display_surface.blit(text, text_rect)
            pygame.display.update()
            self.clock.tick(FRAMERATE)
            
    def show_victory_screen(self):
        font = pygame.font.Font('fonts/pixel_font.ttf', 150)
        text = font.render('VICTORY', True, (255, 215, 0))  # Vàng kim
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

        particles = []
        for _ in range(200):  # Tạo 100 hạt ban đầu
            x = randint(0, WINDOW_WIDTH)
            y = randint(0, WINDOW_HEIGHT)  # Giới hạn pháo hoa ở nửa trên
            color = (randint(50, 255), randint(50, 255), randint(50, 255))  # Màu ngẫu nhiên
            speed = [randint(-5, 5), randint(-3, -1)]  # Tốc độ di chuyển ngẫu nhiên
            lifetime = 5000  # Thời gian tồn tại của hạt
            particles.append({'pos': [x, y], 'color': color, 'speed': speed, 'lifetime': lifetime})

        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 5000:  # Hiển thị trong 2 giây
            self.display_surface.fill((0, 0, 0))  # Nền màu đen
            self.display_surface.blit(text, text_rect)
            for particle in particles[:]:
            # Vẽ hạt
                pygame.draw.circle(self.display_surface, particle['color'], (int(particle['pos'][0]), int(particle['pos'][1])), 5)
            
            # Cập nhật vị trí hạt
                particle['pos'][0] += particle['speed'][0]
                particle['pos'][1] += particle['speed'][1]
            
            # Giảm thời gian tồn tại
                particle['color'] = (
                    max(0, particle['color'][0] - 1),
                    max(0, particle['color'][1] - 1),
                    max(0, particle['color'][2] - 1),
                )  # Làm mờ dần màu
            
            # Loại bỏ hạt nếu hết thời gian tồn tại
                if particle['lifetime'] <= 0:
                    particles.remove(particle)
            pygame.display.update()
            self.clock.tick(FRAMERATE)
    
    def restart_game(self):
    # Reset các nhóm sprite
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.bullet_sprites.empty()
        self.enemy_sprites.empty()
    # Reset player và các thực thể
        self.setup()
        self.audio['music'].stop()
    # Quay lại menu
        self.show_menu = True
        
    
    def run(self):
        while self.running:
            if self.show_menu:
                self.menu.draw()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    action = self.menu.handle_event(event)
                    if action == "START":
                        self.setup()
                        self.show_menu = False
                    elif action == "EXIT":
                        self.running = False
                    
            else:   
                dt = self.clock.tick(FRAMERATE) / 1000 
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False 
            
                # update
                self.bee_timer.update()
                self.all_sprites.update(dt)
                self.collision()

                # draw 
                self.display_surface.fill(BG_COLOR)
                self.all_sprites.draw(self.player.rect.center)
                pygame.display.update()
        
        pygame.quit()
 
if __name__ == '__main__':
    game = Game()
    game.run()
