import { addons } from '@storybook/manager-api';
import { themes } from '@storybook/theming';

addons.setConfig({
  theme: themes.light,
  panelPosition: 'bottom',
  selectedPanel: 'storybook/docs/panel',
  sidebar: {
    showRoots: true,
    collapsedRoots: ['other'],
  },
});