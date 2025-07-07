// ABOUTME: Widget registration system for managing and retrieving widget components
// ABOUTME: Provides centralized registry for all available widget types

import { WidgetComponent, WidgetRegistration } from './base-widget';

class WidgetRegistryClass {
  private widgets: Map<string, WidgetRegistration> = new Map();

  register(registration: WidgetRegistration): void {
    if (!registration.type || !registration.component) {
      throw new Error('Widget registration must include type and component');
    }

    if (this.widgets.has(registration.type)) {
      console.warn(`Widget type "${registration.type}" is already registered. Overwriting...`);
    }

    this.widgets.set(registration.type, registration);
  }

  unregister(type: string): boolean {
    return this.widgets.delete(type);
  }

  get(type: string): WidgetRegistration | undefined {
    return this.widgets.get(type);
  }

  getComponent(type: string): WidgetComponent | undefined {
    const registration = this.widgets.get(type);
    return registration?.component;
  }

  getAll(): WidgetRegistration[] {
    return Array.from(this.widgets.values());
  }

  getByCategory(category: string): WidgetRegistration[] {
    return Array.from(this.widgets.values()).filter(
      widget => widget.category === category
    );
  }

  getCategories(): string[] {
    const categories = new Set<string>();
    this.widgets.forEach(widget => {
      if (widget.category) {
        categories.add(widget.category);
      }
    });
    return Array.from(categories);
  }

  validateConfiguration(type: string, config: Record<string, any>): boolean {
    const registration = this.widgets.get(type);
    if (!registration) {
      return false;
    }

    // Use custom validation if provided
    if (registration.component.validateConfiguration) {
      return registration.component.validateConfiguration(config);
    }

    // Basic validation using config schema if provided
    if (registration.configSchema) {
      // Here you could implement JSON schema validation
      // For now, just check required fields
      const requiredFields = Object.entries(registration.configSchema)
        .filter(([_, schema]: [string, any]) => schema.required)
        .map(([field]) => field);

      return requiredFields.every(field => config[field] !== undefined);
    }

    return true;
  }

  clear(): void {
    this.widgets.clear();
  }
}

// Create singleton instance
export const WidgetRegistry = new WidgetRegistryClass();

// Export for convenience
export type { WidgetRegistration, WidgetComponent } from './base-widget';