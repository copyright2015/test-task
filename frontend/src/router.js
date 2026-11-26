import { createRouter, createWebHistory } from 'vue-router'
import CampaignsView from './views/CampaignsView.vue'
import CreateCampaignView from './views/CreateCampaignView.vue'
import EditCampaignView from './views/EditCampaignView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: CampaignsView },
    { path: '/campaigns/new', component: CreateCampaignView },
    { path: '/campaigns/:id/edit', component: EditCampaignView },
  ],
})
