import axios from "axios";
import { NextResponse } from "next/server";

interface patchUserProfileProps {
	email?: string;
	nom?: string;
	prenom?: string;
	sexe?: string;
	birthday?: string;
}

export const getUserProfile = async (session: any) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/users/me`,
			method: "GET",
			headers: {
				"Content-Type": "application",
				Authorization: `Bearer ${session?.accessToken}`,
			},
		});
		return response.data;
	} catch (error) {
		NextResponse.json({ error });
	}
};

export const postGenresUser = async (session: any, genres: string[]) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/genreusers/`,
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${session?.accessToken}`,
			},
			data: JSON.stringify({
				genre_id: genres,
			}),
		});
		if (response.status === 200) {
			alert("Genres enregistrés avec succès !");
		}
	} catch (error) {
		NextResponse.json({ error });
	}
};

export const patchUserProfile = async (session: any, userData: patchUserProfileProps) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/users/me`,
			method: "PUT",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${session?.accessToken}`,
			},
			data: userData,
		});
		if (response.status === 200) {
			console.log("Informations users mise à jour avec succès !");
		}
	} catch (error) {
		console.error("Erreur lors de la mise à jour du profil utilisateur:", error);
		if (axios.isAxiosError(error)) {
			console.error("Détails de l'erreur:", error.response?.data);
		}
	}
};

export const deleteUserProfile = async (session: any) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/users/me`,
			method: "DELETE",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${session?.accessToken}`,
			},
		});
		if (response.status === 200) {
			setTimeout(() => {
				alert("User supprimé avec succès !");
			}, 2000); // Délai de 2 secondes
			return { success: true };
		}
	} catch (error) {
		console.error("Erreur lors de la suppression du profil utilisateur:", error);
		if (axios.isAxiosError(error)) {
			console.error("Détails de l'erreur:", error.response?.data);
		}
		return { success: false };
	}
};

interface updateUserPasswordProps {
	current_password: string;
	new_password: string;
}

export const updateUserPassword = async (session: any, userData: updateUserPasswordProps) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/users/me/password`,
			method: "PUT",
			headers: {
				ContentType: "application/json",
				Authorization: `Bearer ${session?.accessToken}`,
			},
			data: userData,
		});
		if (response.status === 200) {
			console.log("Informations users mise à jour avec succès !");
		}
	} catch (error) {
		console.error("Erreur lors de la mise à jour du profil utilisateur:", error);
		if (axios.isAxiosError(error)) {
			console.error("Détails de l'erreur:", error.response?.data);
		}
	}
};

interface movieUserProps {
	movie_id: number;
	note: number;
	saved: boolean;
}

export const getMovieUser = async (session: any) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/movieusers/`,
			method: "GET",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${session?.accessToken}`,
			},
		});
		return response.data;
	} catch (error) {
		console.error("Erreur lors de la récupération des films user:", error);
		throw error;
	}
};

export const getMovieUserBy = async (session: any, id: number) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/movieusers/${id}`,
			method: "GET",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${session?.accessToken}`,
			},
		});
		if (response.status !== 200) {
			return { success: false };
		}
		return response.data;
	} catch (error) {
		console.error("Erreur lors de la récupération des films user:", error);
		return { movie_id: id, note: 0, saved: false };
	}
};

export const postMovieUser = async (session: any, userData: movieUserProps) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/movieusers/`,
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${session?.accessToken}`,
			},
			data: userData,
		});
		if (response.status === 200) {
			return { success: true };
		}
	} catch (error) {
		console.error("Erreur lors de la mise à jour du profil utilisateur:", error);
		throw error;
	}
};

export const updateMovieUser = async (session: any, userData: movieUserProps) => {
	try {
		const apiUrl = process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL;
		const response = await axios({
			url: `${apiUrl}/api/v1/movieusers/`,
			method: "PUT",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${session?.accessToken}`,
			},
			data: userData,
		});
		if (response.status === 200) {
			return response.data;
		}
	} catch (error) {
		console.error("Erreur lors de la mise à jour du profil utilisateur:", error);
		throw error;
	}
};
