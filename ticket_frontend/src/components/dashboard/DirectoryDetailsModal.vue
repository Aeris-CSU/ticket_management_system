<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

const props = withDefaults(defineProps<{ title: string; dismissible?: boolean }>(), { dismissible: true })
const emit = defineEmits<{ close: [] }>()
function close() { if (props.dismissible !== false) emit('close') }
const dialog = ref<HTMLDialogElement | null>(null)
let previousOverflow = ''
let previousFocus: HTMLElement | null = null
onMounted(() => {
  previousFocus = document.activeElement as HTMLElement | null
  previousOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  dialog.value?.showModal()
})
onBeforeUnmount(() => {
  dialog.value?.close()
  document.body.style.overflow = previousOverflow
  previousFocus?.focus()
})
</script>

<template>
  <Teleport to="body">
    <dialog ref="dialog" class="ticket-details-modal directory-details-modal" aria-labelledby="directory-modal-heading" @cancel.prevent="close" @click="($event.target === dialog) && close()">
      <div class="ticket-modal-surface">
        <header class="ticket-modal-header"><h2 id="directory-modal-heading">{{ title }}</h2><button class="ticket-modal-close" type="button" aria-label="Close dialog" :disabled="dismissible === false" autofocus @click="close">✕</button></header>
        <div class="ticket-modal-body"><slot /></div>
      </div>
    </dialog>
  </Teleport>
</template>
