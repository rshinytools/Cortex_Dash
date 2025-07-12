// ABOUTME: Authentication API client functions
// ABOUTME: Handles login, password recovery, and password reset operations

import { apiClient, getErrorMessage } from './client';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface PasswordRecoveryRequest {
  email: string;
}

export interface PasswordResetRequest {
  token: string;
  password: string;
}

export interface MessageResponse {
  message: string;
}

export const authApi = {
  // Login user
  async login(data: LoginRequest): Promise<LoginResponse> {
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await apiClient.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Request password recovery email
  async requestPasswordRecovery(email: string): Promise<MessageResponse> {
    try {
      const response = await apiClient.post<MessageResponse>(`/password-recovery/${email}`);
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  // Reset password with token
  async resetPassword(data: PasswordResetRequest): Promise<MessageResponse> {
    try {
      const response = await apiClient.post<MessageResponse>('/reset-password/', data);
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },

  // Get password recovery HTML content (for preview/testing)
  async getPasswordRecoveryHtmlContent(email: string): Promise<string> {
    try {
      const response = await apiClient.post<string>(`/password-recovery-html-content/${email}`);
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  },
};