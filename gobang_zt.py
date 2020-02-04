# - * - coding: utf-8 - * -

# 采集→统计→评估→决策

# 待解决：
# 统计：连珠判断（隔一个）
# 评估：双活三
# 决策：同级同分的选择（random）
#     *决策网络（多步预测）
import pygame

pygame.init()

# dimensions, lengths
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 680
BOARD_SIZE = 19              # 棋盘阶数，每格宽度
CELL_SIZE = 30
GRID_START_X = 15
GRID_START_Y = 15

# storing the board as numbers
EMPTY_PIECE = 0   # 交叉点状态
AI_PIECE = 1
PLAYER_PIECE = 2

STATUS_RUNNING = 0
STATUS_STOPPED = 1

# images/surfaces
TITLE_TEXT_IMG = pygame.image.load('face01.bmp')
TITLE_TEXT_IMG.set_colorkey((0, 0, 0))

WHITE_IMG = pygame.transform.scale(pygame.image.load('white.png'), (35, 35))
BLACK_IMG = pygame.transform.scale(pygame.image.load('black.png'), (35, 35))

BOARD_IMG = pygame.Surface((570, 570))
BOARD_IMG.fill((240, 200, 0))
L = GRID_START_X + BOARD_SIZE * CELL_SIZE - CELL_SIZE
for n in range(GRID_START_X, SCREEN_HEIGHT, CELL_SIZE):
    pygame.draw.line(BOARD_IMG, (0, 0, 0), (GRID_START_X, n), (L, n), 1)
    pygame.draw.line(BOARD_IMG, (0, 0, 0), (n, GRID_START_Y), (n, L), 1)
pygame.draw.rect(BOARD_IMG, (0, 0, 0),
                 (GRID_START_X-1, GRID_START_Y-1, L + 3-GRID_START_X, L + 3-GRID_START_Y), 1)

# fonts
SCORE_FONT = pygame.font.Font(None, 16)
WIN_FONT = pygame.font.Font(None, 96)
STR_FONT = pygame.font.Font(None, 32)

def draw_text(surface, font, color, text, x, y):
    surface.blit(font.render(text, True, color), (x, y))


# 四个方向 0:横，1:竖，2:左上→右下，3:右上→左下
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (-1, 1))
X = 0
Y = 1


def is_winning_piece(board, x, y, piece_type):  # 新落子坐标，落棋人
    for direction in DIRECTIONS:  # 横竖斜
        # 先反向
        pieces_found = 0
        for orientation in (-1, 1):
            search_x = x + orientation*direction[X]
            search_y = y + orientation*direction[Y]
            for i in range(5):
                if (search_x < 0
                        or search_x >= BOARD_SIZE
                        or search_y < 0
                        or search_y >= BOARD_SIZE
                        or board[search_y][search_x] != piece_type):
                    break
                pieces_found += 1
                search_x += orientation * direction[X]
                search_y += orientation * direction[Y]
        if pieces_found + 1 >= 5:
            return True
    return False


def get_flag_beads(board, x, y, piece_type, direction):
    num_connected = 1
    num_empty_sides = 0
    offset = DIRECTIONS[direction]
    for orientation in (-1, 1):
        search_x = x + orientation * offset[X]
        search_y = y + orientation * offset[Y]
        for i in range(5):
            if (search_x < 0
                    or search_x >= BOARD_SIZE
                    or search_y < 0
                    or search_y >= BOARD_SIZE):
                break
            if board[search_y][search_x] != piece_type:
                num_empty_sides += (board[search_y][search_x] == EMPTY_PIECE)  # 是空格加一
                break
            num_connected += 1
            search_x += orientation * offset[X]
            search_y += orientation * offset[Y]
    if num_connected > 5:
        num_connected = 5
    #if (num_empty_sides != 2 and piece_type == AI_PIECE):
        # print(x, y)
        # print(x, y, "direction", direction, "num_connected", num_connected, "pNum", num_empty_sides)
    return [num_connected, num_empty_sides]


ASSESS_WIN = 2  # 己胜，必胜（堵），计算
ASSESS_ANS = 1
ASSESS_COUNT = 0


def get_assess_value(countList):
    # -----评分标准-----#
    #      对方     己胜
    # 五子: 已胜 200 己胜
    # 活四: 必堵 100 必胜
    # 单四: 必堵 70  必胜
    # 活三: 计算 60  计算
    # 单三: 计算 30  计算
    # 活二: 计算 20  计算
    # 单二: 计算 15  计算
    # 活一: 计算 5  计算
    # 单一: 计算 3   计算
    assess = 0
    value = 0
    if ([5, 2] in countList) or ([5, 1] in countList) or ([5, 0] in countList):
        assess = ASSESS_WIN
        value = 200
    elif [4, 2] in countList:
        assess = ASSESS_ANS
        value = 100
    else:  # 计算
        value += countList.count([4, 1]) * 70
        value += countList.count([3, 2]) * 60
        value += countList.count([3, 1]) * 30
        value += countList.count([2, 2]) * 20
        value += countList.count([2, 1]) * 15
        # value += countList.count([2, 2]) * 5
        # value += countList.count([2, 1]) * 3
        assess = ASSESS_COUNT
    return (assess, value)


class Gobang(object):
    def __init__(self, start_x, start_y, playerIsBlack):
        self.start_x = start_x
        self.start_y = start_y
        self.playerOrder = list()
        self.aiOrder = list()
        self.grid_init(playerIsBlack)
        self.draw_assess_scores = True      # 评估价值显示状态
        self.status = STATUS_RUNNING        # 0游戏，1暂停
        self.winner = 0
        
    def grid_init(self, playerIsBlack):
        self.grid = []
        for y in range(BOARD_SIZE):
            line = [EMPTY_PIECE] * BOARD_SIZE
            self.grid.append(line)
        self.assessList = []
        for y in range(BOARD_SIZE):
            line = []
            for x in range(BOARD_SIZE):
                assess = Assess(x, y)
                line.append(assess)
            self.assessList.append(line)
        self.bMaxAssess = 0
        self.bMaxValue = 0
        self.bpX = 9
        self.bpY = 9
        self.wMaxAssess = 0
        self.wMaxValue = 0
        self.wpX = -1
        self.wpY = -1
        self.SumValue = 0
        self.pX = -1
        self.pY = -1
        if (playerIsBlack):
            #self.grid[9][9] = PLAYER_PIECE
            self.playerImg = BLACK_IMG
            self.aiImg = WHITE_IMG
        else:
            self.grid[9][9] = AI_PIECE
            self.playerImg = WHITE_IMG
            self.aiImg = BLACK_IMG
            self.aiOrder.append((9, 9))

    def draw_chess(self, surface):
        for i in range(len(self.playerOrder)):
            coor = self.playerOrder[i]
            surface.blit(self.playerImg, (self.start_x+coor[0]*CELL_SIZE, self.start_y+coor[1]*CELL_SIZE))
            draw_text(surface, SCORE_FONT, (255, 0, 0), str(i),\
                        self.start_x+coor[0]*CELL_SIZE+int(CELL_SIZE/2), self.start_y+coor[1]*CELL_SIZE+int(CELL_SIZE/2))
        for i in range(len(self.aiOrder)):
            coor = self.aiOrder[i]
            surface.blit(self.aiImg, (self.start_x+coor[0]*CELL_SIZE, self.start_y+coor[1]*CELL_SIZE))
            draw_text(surface, SCORE_FONT, (0, 0, 255), str(i),\
                        self.start_x+coor[0]*CELL_SIZE+int(CELL_SIZE/2),self.start_y+coor[1]*CELL_SIZE+int(CELL_SIZE/2))

    def draw(self, surface):   # 刷新屏幕
        surface.fill((180, 140, 0))
        surface.blit(TITLE_TEXT_IMG, (0, 0))            # 题图
        surface.blit(BOARD_IMG, (self.start_x, self.start_y))  # 棋盘
        self.draw_chess(surface)                    # 棋子
        if len(self.playerOrder) > 0:
            pygame.draw.rect(surface,(255,0,0),(self.start_x+self.playerOrder[-1][0]*CELL_SIZE,\
                                                self.start_y+self.playerOrder[-1][1]*CELL_SIZE,\
                                                self.playerImg.get_size()[0],self.playerImg.get_size()[1]),2)

        if len(self.aiOrder) > 0:
            pygame.draw.rect(surface,(0,0,255),(self.start_x+self.aiOrder[-1][0]*CELL_SIZE,\
                                                self.start_y+self.aiOrder[-1][1]*CELL_SIZE,\
                                                self.aiImg.get_size()[0],self.aiImg.get_size()[1]),2)
        #labels
        surface.blit(self.playerImg,(610,290))
        draw_text(surface,STR_FONT,(255,0,0),"player",650,300)
        surface.blit(self.aiImg,(610,340))
        draw_text(surface,STR_FONT,(0,0,255),"zhang tian",650,350)

        if self.status == STATUS_STOPPED:
            if self.winner == AI_PIECE:
                txt = 'YOU LOSE'
                color = (0, 0, 255)
            else:
                txt = 'YOU WIN'
                color = (255, 0, 0)
            draw_text(surface, WIN_FONT, color, txt, 200, 290)
        
    def grid_assess(self):  # 遍历棋盘
        self.bMaxAssess = 0
        self.bMaxValue = 0
        self.bpX = 9
        self.bpY = 9
        self.wMaxAssess = 0
        self.wMaxValue = 0
        self.wpX = -1
        self.wpY = -1
        self.SumValue = 0
        self.pX = -1
        self.pY = -1
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                if self.grid[y][x] != EMPTY_PIECE:
                    continue
                self.assessList[y][x].assess(self.grid)
                # -----全盘评估-----#
                pnt = self.assessList[y][x]
                # 全盘黑方评估
                if ((pnt.aiAssess > self.bMaxAssess)
                        or ((pnt.aiAssess == self.bMaxAssess) and (pnt.aiValue > self.bMaxValue))):
                    self.bMaxAssess = pnt.aiAssess
                    self.bMaxValue = pnt.aiValue
                    self.bpX = x
                    self.bpY = y
                # 全盘白方评估
                if ((pnt.playerAssess > self.wMaxAssess)
                        or ((pnt.playerAssess == self.wMaxAssess) and (pnt.playerValue > self.wMaxValue))):
                    self.wMaxAssess = pnt.playerAssess
                    self.wMaxValue = pnt.playerValue
                    self.wpX = x
                    self.wpY = y
                # 总分评估
                if pnt.playerValue + pnt.aiValue > self.SumValue:
                    self.SumValue = pnt.playerValue + pnt.aiValue
                    self.pX = x
                    self.pY = y

    def grid_policy(self):  # 决策分析
        if self.bMaxAssess == ASSESS_WIN:
            #print('ASSESS_WIN：', self.bpX, self.bpY)
            return (self.bpX, self.bpY)
        elif self.wMaxAssess == ASSESS_WIN:
            #print('ASSESS_WIN：', self.wpX, self.wpY)
            return (self.bpX, self.bpY)
        elif self.bMaxAssess > ASSESS_COUNT:
            #print('B ASSESS_COUNT：', self.bpX, self.bpY)
            return (self.bpX, self.bpY)
        elif self.bMaxAssess > ASSESS_COUNT:
            #print('W ASSESS_COUNT：', self.wpX, self.wpY)
            return (self.wpX, self.wpY)
        else:
            #print('SUM ASSESS_COUNT：', self.pX, self.pY)
            return (self.pX, self.pY)

    def mouse_down(self, x, y):
        if self.status == STATUS_STOPPED:
            return
        x = int((x-self.start_x-GRID_START_X)/CELL_SIZE + 0.5)
        y = int((y-self.start_y-GRID_START_Y)/CELL_SIZE + 0.5)
        self.playerOrder.append((x, y))
        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            if self.grid[y][x] == EMPTY_PIECE:
                self.grid[y][x] = PLAYER_PIECE
                if is_winning_piece(self.grid, x, y, PLAYER_PIECE):  # 判断是否五子连珠
                    self.winner = PLAYER_PIECE
                    self.status = STATUS_STOPPED
                    return
                self.grid_assess()
                x, y = self.grid_policy()
                self.grid[y][x] = AI_PIECE
                self.aiOrder.append((x, y))
                if is_winning_piece(self.grid, x, y, AI_PIECE):  # 判断是否五子连珠
                    self.winner = AI_PIECE
                    self.status = STATUS_STOPPED
                    return
                self.grid_assess()


class Assess(object):
    # 单点数子与价值计算

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.aiAssess = 0         # 评级
        self.playerAssess = 0
        self.aiValue = 0          # 估值
        self.playerValue = 0
        self.aiCount = [[0, 0], [0, 0], [0, 0], [0, 0]]  # 统计
        self.playerCount = [[0, 0], [0, 0], [0, 0], [0, 0]]  # 统计

    def beads(self, grid):  # 统计：四个方向连子数&活力值
        for direction in range(4):
            self.aiCount[direction] = get_flag_beads(grid, self.x, self.y, AI_PIECE, direction)
            self.playerCount[direction] = get_flag_beads(grid, self.x, self.y, PLAYER_PIECE, direction)

    def assess(self, grid):
        self.beads(grid)  # 得到四个方向连子数
        self.aiAssess, self.aiValue = get_assess_value(self.aiCount)
        self.playerAssess, self.playerValue = get_assess_value(self.playerCount)


# -----主程序-----#
gobang = Gobang(30, 80, (input("请选择持方(执黑输入B，执白输入其他任意字符)：") == "B"))

display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

running = True

while running:
    gobang.draw(display)
    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and gobang.status == STATUS_RUNNING:
                gobang.mouse_down(event.pos[0], event.pos[1])
        if event.type == pygame.QUIT:
            running = False

pygame.quit()