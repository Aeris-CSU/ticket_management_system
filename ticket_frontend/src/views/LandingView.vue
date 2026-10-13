<script setup lang="ts">
import LandingNavbar from '@/components/landing/LandingNavbar.vue'
import HeroSection from '@/components/landing/HeroSection.vue'
import FeaturesSection from '@/components/landing/FeaturesSection.vue'
import AboutSection from '@/components/landing/AboutSection.vue'
import CallToAction from '@/components/landing/CallToAction.vue'
import LandingFooter from '@/components/landing/LandingFooter.vue'
</script>

<template>
  <div class="landing-page">
    <LandingNavbar />
    <main>
      <HeroSection />
      <FeaturesSection />
      <AboutSection />
      <CallToAction />
    </main>
    <LandingFooter />
  </div>
</template>
