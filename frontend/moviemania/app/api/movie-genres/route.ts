"use server";

import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

export async function GET(req: NextRequest) {
	try {
		// Utiliser l'URL interne du container pour l'API route côté serveur
		const response = await axios.get("http://rec_api:8000/genres");
		return NextResponse.json(response.data, { status: 200 });
	} catch (error) {
		console.error("Erreur lors de la récupération des genres:", error);
		return NextResponse.json({ error: "Error fetching movie genres" }, { status: 500 });
	}
}

export async function OPTIONS() {
	return NextResponse.json({ error: "Method not allowed" }, { status: 405 });
}
