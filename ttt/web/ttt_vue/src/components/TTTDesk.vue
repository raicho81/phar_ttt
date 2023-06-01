<script setup>
    defineProps({
        desk: {
            type: Array,
            required: true
        },
        player_mark: {
            type: String,
            required: true
        },
        player_code: {
            type: Number,
            required: true
        },
        next_player_code: {
            type: Number,
            required: true
        }
    })
</script>

<script>
    export default {
        emits: ['makeMove'],
        methods: {
            clickDiv(row_idx, col_idx){
                if (this.desk[row_idx][col_idx] != null){
                    return
                }
                // this.desk[row_idx][col_idx] = this.player_code
                const idx = this.desk.length * row_idx + col_idx + 1
                this.$emit('makeMove', idx)
            }
        }
    }
</script>

<template>
    <div v-for="(row, row_idx) in desk" style="display: flex;">
        <div v-for="(col, col_idx) in row" style="font-size: 30px; border: solid 1px; width: 50px; height: 50px; text-align: center; vertical-align: middle;" @click="clickDiv(row_idx, col_idx)">
            {{ (col == null) ? '' : ((col == this.player_code) ? this.player_mark : (this.player_mark == 'x' ? 'o' : 'x')) }}
        </div>
    </div>
</template>