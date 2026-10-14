<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import TicketDetailsView from '@/views/TicketDetailsView.vue'
import type { Ticket } from '@/types/ticket'

defineProps<{ ticketId: number }>()
const emit = defineEmits<{ close: []; changed: [ticket: Ticket] }>()
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
    <dialog ref="dialog" class="ticket-details-modal ticket-record-modal" aria-labelledby="ticket-modal-heading" @cancel.prevent="emit('close')" @click="($event.target === dialog) && emit('close')">
      <div class="ticket-modal-surface">
        <header class="ticket-modal-header"><div><h2 id="ticket-modal-heading">Ticket Details</h2></div><button class="ticket-modal-close" type="button" aria-label="Close ticket details" autofocus @click="emit('close')">✕</button></header>
        <div class="ticket-modal-body"><TicketDetailsView :ticket-id="ticketId" embedded @changed="emit('changed', $event)" /></div>
      </div>
    </dialog>
  </Teleport>
</template>
