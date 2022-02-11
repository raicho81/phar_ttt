<script setup>
    import TTTDesk from './TTTDesk.vue'
</script>

<script>
export default {
    data() {
        return {
            game_data: {
                player_name: 'Input Your Name Here',
                game_started: false,
                ttt_play_msg: null,
                ttt_player: null,
                game_uuid: null,
                desk_size: 4,
                desk: null,
                game_state: null
            }
        }
    },
    methods: {
        async startNewGame() {
            const res = await fetch(
                `:8080/start/${this.player_name}/${this.game_data.desk_size}`
            )
            game_data = await res.json()
        },
        async makeMove() {

        }
    }
}
</script>

<template>
    <span v-if="!game_data.game_started">
        <p>Player Name <input v-model="game_data.player_name" type="text"/> <button @click="startNewGame">Start New Game</button></p>
    </span>
    <span v-else>
        <p>Game started.</p>
        <TTTDesk :desk="desk"/>
    </span>
</template>
