import axios from "axios";
import { NextResponse } from "next/server";
import { MultipleMovieUserProps } from "@/src/types";

export const getAllMovieGenres = async () => {
	try {
		const apiUrl = process.env.RECOS_API_URL || process.env.NEXT_PUBLIC_RECOS_API_URL;
		const response = await axios({
			url: `${apiUrl}/genres`,
			method: "GET",
			headers: {
				"Content-Type": "application/json",
			},
		});
		if (response.status === 200) {
			return response.data;
		}
	} catch (error) {
		NextResponse.json({ error });
	}
};

export const getMoviesRecommendations = async (session: any) => {
	try {
		const apiUrl = process.env.RECOS_API_URL || process.env.NEXT_PUBLIC_RECOS_API_URL;
		const response = await axios({
			url: `${apiUrl}/recommendations/`,
			method: "GET",
			headers: {
				"Content-Type": "application/json",
				Authorization: `${session?.accessToken}`,
			},
		});
		if (response.status === 200) {
			return response.data;
		}
	} catch (error) {
		NextResponse.json({ error });
	}
};

export const getMovieDetails = async (id: number) => {
	try {
		const apiUrl = process.env.RECOS_API_URL || process.env.NEXT_PUBLIC_RECOS_API_URL;
		const response = await axios({
			url: `${apiUrl}/movies/${id}`,
			method: "GET",
			headers: {
				"Content-Type": "application/json",
			},
		});
		if (response.status === 200) {
			return response.data;
		}
	} catch (error) {
		NextResponse.json({ error });
	}
};

export const getMovieDetailsByTitle = async (query: string) => {
	try {
		console.log("query", query);
		const apiUrl = process.env.RECOS_API_URL || process.env.NEXT_PUBLIC_RECOS_API_URL;
		const response = await axios({
			url: `${apiUrl}/movies/search/?title=${query}`,
			method: "GET",
			headers: {
				"Content-Type": "application/json",
			},
		});
		if (response.status === 200) {
			return response.data;
		}
	} catch (error) {
		NextResponse.json({ error });
	}
};

export const getHydratedMedia = async (movies: MultipleMovieUserProps) => {
	const mediaPromises = movies.data.map(async (movie) => {
		const details = await getMovieDetails(movie.movie_id);
		return {
			...details,
			note: movie.note,
			saved: movie.saved,
		};
	});

	const mediaList = await Promise.all(mediaPromises);

	return mediaList;
};
