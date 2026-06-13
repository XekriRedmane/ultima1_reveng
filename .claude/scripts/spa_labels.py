# SPA-local global routine labels (address -> name). Branch-internal targets
# stay as .Lxxxx local labels; these are the named subroutine entry points.
LBL = {
 0x8956:'OVERLAY_ENTRY',
 0x8984:'LIFTOFF_COUNT',       # "10..9..8.." liftoff countdown loop
 0x8A53:'SPA_LOOP',            # main loop: status, key/idle, dispatch
 0x8AA4:'DISPATCH_PATCH',      # copy handler address from DISPATCH_TBL into the loop
 0x8AB3:'PHYSICS',             # integrate velocity, wrap torus, move actors
 0x8AB8:'PHYSICS_MOVE',        # physics re-entry after a rotation (skip the dock test)
 0x8B5D:'STAR_HAZARD',         # proximity to the central star drains the shield
 0x8BB5:'COLLIDE',             # ran into an actor: bounce + shield damage
 0x8C4F:'DOCK',                # docked at a base: refuel, open spacedoors
 0x8D38:'STOW_SHIP',           # store the current craft into a base berth
 0x8DA2:'CHOOSE_SHIP',         # "Choose thy ship": pick a berthed craft to board
 0x8EAE:'BOARD_SHIP',          # board the chosen craft (set fuel/shield/heading)
 0x8F4C:'LAND',                # land on a planet (shuttle only) -> EXIT_TO_OUT
 0x8FAD:'CMD_THRUST',          # accelerate along the heading
 0x8FFC:'CLAMP_VEL',           # clamp a velocity component to [-8,+8]/[F8,08]
 0x900E:'CMD_RETRO',           # decelerate (reverse thrust)
 0x904E:'CMD_CLOCKWISE',       # rotate heading clockwise
 0x9074:'CMD_COUNTER',         # rotate heading counter-clockwise
 0x909A:'CMD_HYPER_BLOCKED',   # HyperJump only works in front view
 0x90D5:'CMD_SCAN',            # sector-scan (radar) command
 0x90DE:'SECTOR_SCAN',         # draw the 8x8 sector-scan grid + blink the ship
 0x93FE:'RETICLE_DRAW',        # erase/redraw the targeting reticle box
 0x9411:'RETICLE_PLOT',        # plot the reticle box at (ZP_RET_X,ZP_RET_Y)
 0x9452:'RNG_TO_PIXEL',        # convert RNG state into a star pixel column
 0x9461:'RNG_STEP_PIX',        # one Fibonacci RNG step -> signed pixel delta
 0x9477:'IDLE_TICK',           # cursor flash + one starfield pan step
 0x9486:'IDLE_POLL',           # poll for a key with a starfield-animated timeout
 0x9497:'STARFIELD_PAN',       # pan + redraw the 42-star field one frame
 0x95BF:'SCAN_CENTER',         # recenter the radar pan to the ship
 0x95CF:'PAN_RESET',           # reset the pan deltas to centre
 0x95E1:'PAN_WEST', 0x95FC:'PAN_EAST', 0x9617:'PAN_NORTH', 0x9632:'PAN_SOUTH',
 0x964D:'CMD_FIRE',            # fire: hit-test the reticle against the enemy
 0x96BD:'EXPLODE',             # play the hit/explosion flash
 0x96E2:'HIT_ENEMY',           # award exp, INC PLR_VESSELS, the Space Ace gate
 0x97B9:'RETICLE_RESET',       # restore reticle to centre after a shot
 0x97BB:'RETICLE_STROKE',      # stroke the two crosshair diagonals (colour in A)
 0x97CB:'DRAW_CROSSHAIR',
 0x97D8:'MSG_NOFUEL',          # "Not enough fuel!"
 0x97EE:'BEEP_BAD',            # bad-key beep (font '?' + flush)
 0x97F9:'CMD_HYPER',           # HyperJump: the light-speed warp animation
 0x98FE:'CMD_VIEW',            # toggle front view <-> overhead nav view
 0x99CB:'VIEW_BLOCKED',        # "must eliminate all enemy craft first"
 0x99FE:'CMD_ZTATS',
 0x9A01:'VIEW_WIPE',           # clear + redraw the viewport border
 0x9A3D:'ENEMY_AI',            # move the enemy reticle / decide to fire back
 0x9AC0:'ALIEN_FIRES',         # enemy shot: maybe hit the player, drain shield
 0x9B9C:'DRAW_SHOT',           # stroke a laser line to the reticle
 0x9BAC:'ENEMY_PROJECT',       # project the enemy onto the front view and draw it
 0x9C53:'CELL_DECODE',         # decode the grid cell at (ZP_CX,ZP_CY) into quadrants
 0x9C87:'GRID_ROW_OFF_DATA',   # (data) 8-entry row offsets into the enemy grid
 0x9C92:'RND_BASE_POS',        # random base position on the torus
 0x9CA7:'RND_ACTOR_POS',       # random actor position on the torus
 0x9CBC:'RND_SECTOR',          # random sector cell (mod 10)
 0x9CBE:'RND_RANGE',           # A := RND mod A
 0x9CD4:'RNG_STEP',            # one Fibonacci RNG step on ZP_RNG
 0x9CE2:'ACTOR_DIST',          # squared distance between two actor slots
 0x9D89:'DRAW_ALL_ACTORS',     # draw every actor + the ship into the nav view
 0x9D9E:'DRAW_SHIP_NAV',       # draw the player ship marker in the nav view
 0x9DB9:'DRAW_ACTOR_NAV',      # draw one actor marker in the nav view
 0x9DD0:'BLIT_SETUP',          # set draw mode and fall into the shape blitter
 0x9DE1:'BLIT_SHAPE_AT',       # XOR-blit a shape at (ZP_CX,ZP_CY)
 0x9F2E:'SHAPE_PRESHIFT',      # pre-shift a shape into hi-res byte alignment
 0x9F7F:'PLACE_ACTORS',        # populate the actor table from the current cell
 0xA107:'MUL8_FIXED',          # 8x8 -> 16-bit fixed-point multiply (projection)
 0xA123:'DIV16',               # 16/8 fixed-point divide (projection)
 0xA154:'FUEL_BURN',           # subtract A from PLR_FUEL, clamp at 0
 0xA182:'WIN_STATS_DRAW',      # draw the Shld|Fuel|Exp|Coin status panel
 0xA1BD:'SPEND_TURN',          # JSR TICK with a fixed cost (per action)
}
