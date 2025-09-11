"use server";

import axios from "axios";
import { error } from "console";

interface CheckUserProps {
	email: string;
}

export async function checkUserService(userData: CheckUserProps) {
	try {
		// Utiliser l'URL côté serveur pour les Server Actions
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/users/check`,
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			data: JSON.stringify({ ...userData }),
		});
		return response.data;
	} catch (axiosError) {
		console.error("Error checking user:", axiosError);
		return { error: "Failed to check user" };
	}
}

interface RegisterUserProps {
	email: string;
	password: string;
	genres: number[];
}

export async function registerUserService(userData: RegisterUserProps) {
	try {
		// Utiliser l'URL côté serveur pour les Server Actions
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/users/open`,
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			data: JSON.stringify({ ...userData }),
		});
		return response.data;
	} catch (axiosError) {
		console.error("Erreur lors de l'enregistrement de l'utilisateur :", axiosError);
		return { error: "Failed to register user" };
	}
}

interface LoginUserProps {
	email: string;
	password: string;
}

export async function loginUserService(userData: LoginUserProps) {
	try {
		// Utiliser l'URL côté serveur pour les Server Actions
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios.post(
			`${apiUrl}/api/v1/login/access-token`,
			userData, // Utilise directement l'objet
			{
				headers: {
					"Content-Type": "application/x-www-form-urlencoded",
				},
			}
		);
		return response.data;
	} catch (error) {
		console.error("loginUserService error", error);
		return { error: "An error occurred while logging in" };
	}
}
